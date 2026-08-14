"""
Test generation — owned by AI/ML Engineer.

Consumes List[ParsedChunk] → produces TestResult schema (CONTRACT.md §3).

HOW TO HOOK IN (AI/ML team):
  1. Implement generate_tests() below
  2. In main.py _run_analysis(), after explanation stage:
       from .ai.test_gen import generate_tests
       tests = await asyncio.to_thread(generate_tests, chunks, job.working_dir)
       store_tests(analysis_dict, tests)
       job_manager.update_status(job_id, "testing", progress=92)
"""
import logging
from typing import List, Dict

from ..models.contract import ParsedChunk
from .groq_client import chat

logger = logging.getLogger(__name__)

# ── CONTRACT.md TestResult schema ────────────────────────────────────
# {
#   "test_files":       [{ "file": str, "source": str }],
#   "coverage_percent": float,
#   "passed":           int,
#   "failed":           int,
#   "log":              str
# }


def generate_tests(chunks: List[ParsedChunk]) -> Dict:
    """
    Generate unit tests for all function-type parsed chunks.

    Args:
        chunks: ParsedChunks from Backend parsing stage.

    Returns:
        TestResult dict matching CONTRACT.md §3.
        Always returns valid shape even on partial failure.
    """
    test_files = []

    function_chunks = [c for c in chunks if c.type == "function"]

    for chunk in function_chunks:
        try:
            test_source = _generate_test_for_function(chunk)
            if test_source:
                test_filename = f"test_{chunk.name}.py"
                test_files.append({
                    "file":   test_filename,
                    "source": test_source,
                })
        except Exception as e:
            logger.error("Test gen failed for %s::%s: %s", chunk.file, chunk.name, e)

    # Coverage and pass/fail counts are populated by Backend test runner
    # after actually executing the generated tests (Phase 5)
    return {
        "test_files":       test_files,
        "coverage_percent": 0.0,   # filled in by test_runner.py after execution
        "passed":           0,
        "failed":           0,
        "log":              "",
    }


def _generate_test_for_function(chunk: ParsedChunk) -> str:
    """Generate a pytest test for a single function."""
    source_preview = chunk.source[:1500] if len(chunk.source) > 1500 else chunk.source

    system = (
        "You are a test engineer. Write a pytest unit test for the given function. "
        "Rules:\n"
        "- Import the function correctly based on its file path\n"
        "- Test at least one happy path and one edge case\n"
        "- Use assert statements\n"
        "- Output ONLY valid Python code, no explanation, no markdown fences\n"
        "- Never use Mock unless strictly necessary"
    )
    user = (
        f"File: {chunk.file}\n"
        f"Language: {chunk.language}\n\n"
        f"{source_preview}"
    )

    return chat(system, user, max_tokens=600)
