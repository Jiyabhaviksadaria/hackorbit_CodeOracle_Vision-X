"""
Result aggregator — Phase 6.
Owned by API/Integration Engineer.

Combines outputs from all pipeline stages into the single
GET /api/jobs/{job_id}/result response defined in CONTRACT.md.

Each stage stores its result in job.analysis_data under these KEYS:
  "explanation"       → dict matching Explanation schema
  "dependency_graph"  → dict matching DepGraph schema
  "tests"             → dict matching TestResult schema
  "refactor"          → dict matching RefactorResult schema

Partial results are always returned — a missing stage gives the
empty-but-valid structure from CONTRACT.md, never null/error.
"""
from typing import Dict, Any, Optional


# ── Safe defaults ────────────────────────────────────────────────────
_EMPTY_EXPLANATION = {"modules": [], "functions": []}
_EMPTY_DEP_GRAPH   = {"nodes": [], "edges": []}
_EMPTY_TESTS       = {"test_files": [], "coverage_percent": 0.0, "passed": 0, "failed": 0, "log": ""}
_EMPTY_REFACTOR    = {"files": []}


def aggregate_results(analysis_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge all stage outputs into the CONTRACT.md result shape.

    Resilient: missing / None values from any stage fall back to
    empty-but-valid contract defaults so Frontend never crashes.

    Args:
        analysis_data: The job's analysis_data dict (may be None or partial).

    Returns:
        Full result dict matching CONTRACT.md §3.
    """
    if not analysis_data:
        return {
            "explanation":       _EMPTY_EXPLANATION,
            "dependency_graph":  _EMPTY_DEP_GRAPH,
            "tests":             _EMPTY_TESTS,
            "refactor":          _EMPTY_REFACTOR,
        }

    return {
        "explanation":      analysis_data.get("explanation")      or _EMPTY_EXPLANATION,
        "dependency_graph": analysis_data.get("dependency_graph") or _EMPTY_DEP_GRAPH,
        "tests":            analysis_data.get("tests")            or _EMPTY_TESTS,
        "refactor":         analysis_data.get("refactor")         or _EMPTY_REFACTOR,
    }


def store_dep_graph(analysis_data: Dict[str, Any], dep_graph: Dict) -> None:
    """Write dependency graph result into analysis_data in-place."""
    analysis_data["dependency_graph"] = dep_graph


def store_explanation(analysis_data: Dict[str, Any], explanation: Dict) -> None:
    """Write explanation result into analysis_data in-place."""
    analysis_data["explanation"] = explanation


def store_tests(analysis_data: Dict[str, Any], tests: Dict) -> None:
    """Write test result into analysis_data in-place."""
    analysis_data["tests"] = tests


def store_refactor(analysis_data: Dict[str, Any], refactor: Dict) -> None:
    """Write refactor result into analysis_data in-place."""
    analysis_data["refactor"] = refactor
