import pytest
import os
import tempfile
from pathlib import Path

from backend.app.parsing.repository_analyzer import RepositoryAnalyzer
from backend.app.parsing.contract_adapter import ParsedChunkAdapter
from backend.app.models.repository import Language
from backend.app.ai.explainer import generate_explanations
from backend.app.ai.test_gen import generate_unit_tests
from backend.app.ai.refactor import generate_refactored_code
from backend.app.testing.test_runner import TestRunner, TestRunResult

def test_real_backend_ai_pipeline_integration():
    """
    Real End-to-End Integration Test:
    Backend RepositoryAnalyzer → ParsedChunkAdapter → AI Explainer/TestGen/Refactor → Backend TestRunner.
    Verifies that initial test coverage (50%) is dynamically improved to 100% via the AI coverage feedback loop.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Path(temp_dir)
        sample_file = repo / "calculator.py"
        sample_file.write_text(
            "def add(a, b):\n"
            "    return a + b\n\n"
            "def divide(a, b):\n"
            "    if b == 0:\n"
            "        raise ValueError('Zero division')\n"
            "    return a / b\n"
        )

        # 1. Backend Ingestion & Parsing
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(repo)
        assert len(analysis.functions) == 2

        # 2. Backend Contract Adapter
        chunks = ParsedChunkAdapter.from_repository_analysis(
            list(analysis.functions.values()),
            list(analysis.classes.values()),
            Language.PYTHON
        )
        chunks_dict = [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in chunks]
        assert len(chunks_dict) == 2

        # 3. AI Explanation
        explanations = generate_explanations(chunks_dict)
        assert "modules" in explanations
        assert "functions" in explanations

        # 4. Backend TestRunner direct execution test
        runner = TestRunner(timeout_seconds=30)
        test_workspace = runner.create_test_workspace(
            repo,
            {"test_calculator.py": (
                "import sys, os\n"
                "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))\n"
                "from calculator import add, divide\n\n"
                "def test_add():\n"
                "    assert add(1, 2) == 3\n"
            )}
        )
        run_res = runner.run_python_tests(
            test_directory=test_workspace / "tests",
            source_directory=test_workspace / "src",
            measure_coverage=True
        )
        assert run_res.passed >= 1
        runner.cleanup_test_workspace(test_workspace)

        # 5. AI Test Generation & Coverage Improvement Loop via Adapter
        from unittest.mock import patch
        with patch("backend.app.ai.test_gen.call_gemini") as mock_gemini:
            # Iteration 1: Initial partial test suite (50% coverage, missing divide())
            # Iteration 2: Improved test suite targeting uncovered lines [5, 6, 7] (100% coverage)
            mock_gemini.side_effect = [
                '{"test_source": "import sys, os\\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \\"..\\", \\"src\\")))\\nfrom calculator import add\\n\\ndef test_add():\\n    assert add(1, 2) == 3\\n"}',
                '{"test_source": "import sys, os\\nimport pytest\\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \\"..\\", \\"src\\")))\\nfrom calculator import add, divide\\n\\ndef test_add():\\n    assert add(1, 2) == 3\\n\\ndef test_divide():\\n    assert divide(6, 2) == 3.0\\n\\ndef test_divide_zero():\\n    with pytest.raises(ValueError):\\n        divide(1, 0)\\n"}'
            ]
            test_results = generate_unit_tests(chunks_dict, repo_dir=str(repo))
            assert "test_files" in test_results
            assert test_results["initial_coverage"] == 50.0
            assert test_results["coverage_percent"] == 100.0
            assert test_results["passed"] == 3

        # 6. AI Refactoring via Adapter
        with patch("backend.app.ai.refactor.call_gemini") as mock_gemini_refactor:
            mock_gemini_refactor.return_value = '{"refactored_source": "def add(a: int, b: int) -> int:\\n    return a + b\\n\\ndef divide(a: float, b: float) -> float:\\n    if b == 0:\\n        raise ValueError(\\"Zero division\\")\\n    return a / b\\n"}'
            refactor_results = generate_refactored_code(chunks_dict, repo_dir=str(repo))
            assert "files" in refactor_results
            assert len(refactor_results["files"]) >= 1
