import os
import json
from pathlib import Path
from ...testing.test_runner import TestRunner, TestRunResult

def run_tests_and_measure_coverage(repo_dir: str, test_files: list, language: str) -> dict:
    """
    Adapter function wrapping the Backend Engineer's TestRunner class.
    Translates AI module inputs (repo_dir, test_files, language) into calls to TestRunner
    and returns normalized dictionary format matching the CONTRACT.md TestResult schema.
    Also extracts uncovered line numbers from Backend TestRunner's coverage.json.
    """
    result = {
        "test_files": test_files,
        "coverage_percent": 0.0,
        "passed": 0,
        "failed": 0,
        "log": "",
        "uncovered_lines": []
    }

    if not test_files or not repo_dir:
        result["log"] = "No test files generated or repo_dir missing."
        return result

    runner = TestRunner(timeout_seconds=60)
    source_path = Path(repo_dir).resolve()
    
    if not source_path.exists():
        result["log"] = f"Repository directory does not exist: {repo_dir}"
        return result

    # Convert test_files list to Dict[str, str] mapping for TestRunner.create_test_workspace
    test_files_dict = {tf["file"]: tf["source"] for tf in test_files if "file" in tf and "source" in tf}
    if not test_files_dict:
        result["log"] = "No valid test file dict items provided."
        return result

    try:
        workspace_path = runner.create_test_workspace(source_path, test_files_dict)
        test_dir = workspace_path / "tests"
        src_dir = workspace_path / "src"

        if language == "python":
            run_res: TestRunResult = runner.run_python_tests(
                test_directory=test_dir,
                source_directory=src_dir,
                measure_coverage=True
            )
        else:
            run_res: TestRunResult = runner.run_javascript_tests(
                test_directory=test_dir,
                package_json_dir=src_dir
            )

        result["passed"] = run_res.passed
        result["failed"] = run_res.failed + run_res.errors
        result["coverage_percent"] = round(run_res.coverage_percent, 1)
        result["log"] = (run_res.stdout or "") + ("\n" + run_res.stderr if run_res.stderr else "")

        # Extract uncovered line numbers from Backend TestRunner's coverage.json if available
        coverage_file = workspace_path / "coverage.json"
        uncovered = []
        if coverage_file.exists():
            try:
                with open(coverage_file, "r", encoding="utf-8") as cf:
                    cov_data = json.load(cf)
                files_dict = cov_data.get("files", {})
                for fdata in files_dict.values():
                    missing = fdata.get("missing_lines", [])
                    uncovered.extend(missing)
            except Exception:
                pass
        result["uncovered_lines"] = sorted(list(set(uncovered)))

        runner.cleanup_test_workspace(workspace_path)
    except Exception as e:
        result["log"] = f"Test execution adapter error: {str(e)}"
        result["failed"] = len(test_files)

    return result
