"""
Refactor generation — owned by AI/ML Engineer.

Consumes List[ParsedChunk] → produces RefactorResult schema (CONTRACT.md §3).

HOW TO HOOK IN (AI/ML team):
  1. Implement generate_refactor() below
  2. In main.py _run_analysis(), after testing stage:
       from .ai.refactor import generate_refactor
       refactor = await asyncio.to_thread(generate_refactor, chunks)
       store_refactor(analysis_dict, refactor)
       job_manager.update_status(job_id, "refactoring", progress=96)
"""
import logging
from typing import List, Dict

from ..models.contract import ParsedChunk
from .groq_client import chat

logger = logging.getLogger(__name__)

# ── CONTRACT.md RefactorResult schema ────────────────────────────────
# {
#   "files": [{
#     "original_file":      str,
#     "refactored_source":  str,
#     "breaking_changes":   [str]   ← MUST be present, even if empty []
#   }]
# }


def generate_refactor(chunks: List[ParsedChunk]) -> Dict:
    """
    Generate modernised/refactored versions of all source files.

    Per RULES.md:
      - Refactor must preserve function signatures unless flagged as breaking
      - breaking_changes MUST be present even if empty list (no silent refactors)

    Args:
        chunks: ParsedChunks from Backend parsing stage.

    Returns:
        RefactorResult dict matching CONTRACT.md §3.
        Always returns valid shape even on partial failure.
    """
    # Group chunks by file
    files: Dict[str, List[ParsedChunk]] = {}
    for chunk in chunks:
        files.setdefault(chunk.file, []).append(chunk)

    result_files = []

    for file_path, file_chunks in files.items():
        try:
            refactored_source, breaking_changes = _refactor_file(file_path, file_chunks)
            result_files.append({
                "original_file":     file_path,
                "refactored_source": refactored_source,
                "breaking_changes":  breaking_changes,  # always present per RULES.md
            })
        except Exception as e:
            logger.error("Refactor failed for %s: %s", file_path, e)
            result_files.append({
                "original_file":     file_path,
                "refactored_source": "",
                "breaking_changes":  [f"Refactor unavailable: {e}"],
            })

    return {"files": result_files}


def _refactor_file(file_path: str, chunks: List[ParsedChunk]) -> tuple:
    """
    Refactor a single file. Returns (refactored_source, breaking_changes).
    """
    # Reconstruct approximate file source from chunks
    combined_source = "\n\n".join(c.source for c in chunks)
    # Truncate to stay within token budget per RULES.md
    if len(combined_source) > 3000:
        combined_source = combined_source[:3000] + "\n# ... (truncated)"

    system = (
        "You are a senior software engineer modernising legacy code. "
        "Refactor the given code following these rules:\n"
        "1. Improve readability, naming, and structure\n"
        "2. Use modern language idioms\n"
        "3. Do NOT change function signatures unless absolutely necessary\n"
        "4. If you do change a signature, add it to the breaking_changes list\n"
        "5. Return a JSON object with keys:\n"
        '   "refactored_source": the complete refactored code as a string\n'
        '   "breaking_changes": list of strings describing any signature changes\n'
        "6. Output ONLY valid JSON, no markdown fences"
    )
    user = f"File: {file_path}\n\n{combined_source}"

    import json
    raw = chat(system, user, max_tokens=2000)

    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
        return (
            data.get("refactored_source", combined_source),
            data.get("breaking_changes", []),
        )
    except (json.JSONDecodeError, AttributeError):
        # Non-fatal — return original source with a warning
        return combined_source, ["Refactor response could not be parsed — original returned"]
