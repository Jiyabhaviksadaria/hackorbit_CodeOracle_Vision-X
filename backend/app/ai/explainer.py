"""
Explanation generation — owned by AI/ML Engineer.

Consumes List[ParsedChunk] → produces Explanation schema (CONTRACT.md §3).

HOW TO HOOK IN (AI/ML team):
  1. Implement generate_explanation() below
  2. In main.py _run_analysis(), after dep graph stage:
       from .ai.explainer import generate_explanation
       explanation = await asyncio.to_thread(generate_explanation, chunks)
       store_explanation(analysis_dict, explanation)
       job_manager.update_status(job_id, "explaining", progress=88)
"""
import logging
from typing import List, Dict

from ..models.contract import ParsedChunk
from .groq_client import chat

logger = logging.getLogger(__name__)

# ── CONTRACT.md Explanation schema ───────────────────────────────────
# {
#   "modules":   [{ "file": str, "summary": str }],
#   "functions": [{ "file": str, "name": str, "summary": str,
#                   "params": [str], "returns": str }]
# }


def generate_explanation(chunks: List[ParsedChunk]) -> Dict:
    """
    Generate natural language explanations for all parsed chunks.

    Args:
        chunks: ParsedChunks from Backend parsing stage.

    Returns:
        Explanation dict matching CONTRACT.md §3.
        Always returns valid shape even on partial failure.
    """
    modules   = []
    functions = []

    # Group chunks by file for module-level summaries
    files_seen = {}
    for chunk in chunks:
        files_seen.setdefault(chunk.file, []).append(chunk)

    for file_path, file_chunks in files_seen.items():
        # ── Module summary ───────────────────────────────────────────
        try:
            module_summary = _summarise_module(file_path, file_chunks)
            modules.append({"file": file_path, "summary": module_summary})
        except Exception as e:
            logger.error("Module explanation failed for %s: %s", file_path, e)
            modules.append({"file": file_path, "summary": "Summary unavailable."})

        # ── Function/class summaries ─────────────────────────────────
        for chunk in file_chunks:
            if chunk.type not in ("function", "class"):
                continue
            try:
                summary, params, returns = _summarise_function(chunk)
                functions.append({
                    "file":    chunk.file,
                    "name":    chunk.name,
                    "summary": summary,
                    "params":  params,
                    "returns": returns,
                })
            except Exception as e:
                logger.error("Function explanation failed for %s::%s: %s", file_path, chunk.name, e)
                functions.append({
                    "file":    chunk.file,
                    "name":    chunk.name,
                    "summary": "Explanation unavailable.",
                    "params":  [],
                    "returns": "unknown",
                })

    return {"modules": modules, "functions": functions}


def _summarise_module(file_path: str, chunks: List[ParsedChunk]) -> str:
    """Generate a module-level summary."""
    # Build compact context — never dump full source per RULES.md
    names = [c.name for c in chunks if c.type in ("function", "class")]
    context = f"File: {file_path}\nContains: {', '.join(names[:30])}"

    system = (
        "You are a code documentation assistant. "
        "Write a concise 1-2 sentence summary of what this module does. "
        "Be factual — only describe what's actually in the code."
    )
    return chat(system, context, max_tokens=200)


def _summarise_function(chunk: ParsedChunk):
    """Generate a function-level summary. Returns (summary, params, returns)."""
    # Truncate very long source to stay within token budget
    source_preview = chunk.source[:1500] if len(chunk.source) > 1500 else chunk.source

    system = (
        "You are a code documentation assistant. "
        "Given a function's source code, return a JSON object with keys: "
        '"summary" (1 sentence), "returns" (return type or description). '
        "Be factual. Only describe what the code actually does."
    )
    user = f"Language: {chunk.language}\n\n{source_preview}"

    import json
    raw = chat(system, user, max_tokens=300)

    # Parse JSON response — fall back gracefully if malformed
    try:
        # Strip markdown code fences if present
        clean = raw.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
        return data.get("summary", raw), [], data.get("returns", "unknown")
    except (json.JSONDecodeError, AttributeError):
        return raw[:200], [], "unknown"
