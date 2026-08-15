import os
import json
import logging
from .gemini_client import call_gemini
from .adapters.test_runner_adapter import run_tests_and_measure_coverage

logger = logging.getLogger("codeoracle.test_gen")

MIN_COVERAGE = 60.0
TARGET_COVERAGE = 70.0
MAX_ITERATIONS = 2


def generate_unit_tests(chunks: list, repo_dir: str = None) -> dict:
    """
    Generates unit test suites for source files.
    If repo_dir is supplied, runs an active coverage feedback and repair loop
    up to 2 iterations to achieve >=70% target coverage (>60% competition minimum).
    Conforms to the CONTRACT.md TestResult schema.
    """
    test_result = {
        "test_files": [],
        "coverage_percent": 0.0,
        "passed": 0,
        "failed": 0,
        "log": "",
        "initial_coverage": 0.0,
        "iterations_used": 0
    }

    if not chunks:
        test_result["log"] = "No code chunks to analyze."
        return test_result

    # Normalize chunks if they are Pydantic ParsedChunk objects
    normalized_chunks = [c.model_dump() if hasattr(c, "model_dump") else c for c in chunks]

    # 1. Group chunks by file
    files_data = {}
    for chunk in normalized_chunks:
        file_path = chunk["file"]
        if file_path not in files_data:
            files_data[file_path] = {
                "module": None,
                "functions": [],
                "classes": [],
                "language": chunk["language"]
            }
        
        if chunk["type"] == "module":
            files_data[file_path]["module"] = chunk
        elif chunk["type"] == "class":
            files_data[file_path]["classes"].append(chunk)
        elif chunk["type"] == "function":
            files_data[file_path]["functions"].append(chunk)

    total_passed = 0
    total_failed = 0
    coverage_sum = 0.0
    files_tested_count = 0
    aggregated_logs = []

    for file_path, data in files_data.items():
        language = data["language"]
        file_chunks = data["functions"] + data["classes"]
        module_chunk = data["module"]

        if not file_chunks and not module_chunk:
            continue

        # Determine language config
        if language == "python":
            framework = "pytest"
            base_name = os.path.basename(file_path).replace(".py", "")
            test_file_name = f"test_{base_name}.py"
        else:
            framework = "jest"
            base_name = os.path.basename(file_path).rsplit(".", 1)[0]
            test_file_name = f"{base_name}.test.js"

        # Build comprehensive source context
        if module_chunk:
            source_lines = module_chunk["source"].splitlines()
        else:
            source_lines = ("\n\n".join(c["source"] for c in file_chunks)).splitlines()

        source_snippet = "\n".join(source_lines[:400])
        if len(source_lines) > 400:
            source_snippet += "\n... [TRUNCATED] ..."

        # Generate initial test suite
        test_source = ""
        try:
            initial_prompt = (
                f"You are an expert QA engineer. Generate a comprehensive unit test suite using '{framework}' "
                f"for the code module '{file_path}' (language: {language}).\n\n"
                f"Target Code:\n```\n{source_snippet}\n```\n\n"
                f"Requirements:\n"
                f"1. Code must be syntactically valid and runnable.\n"
                f"2. Correctly import the module. For Python, include path setup:\n"
                f"   import sys, os\n"
                f"   sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))\n"
                f"   from {base_name} import ...\n"
                f"3. IMPORTANT: Identify EVERY function, method, and class in the target code snippet. "
                f"Write at least one dedicated test case for EVERY function and method.\n"
                f"4. Add test cases covering normal execution, boundary values, invalid inputs, empty inputs, nulls, and exception handling.\n"
                f"5. Mock external APIs or network calls.\n"
                f"6. Return a JSON object with a single key 'test_source' containing the raw test file code."
            )
            sys_instruction = "You are a professional testing tool. Output ONLY JSON containing the test source."
            res_str = call_gemini(initial_prompt, system_instruction=sys_instruction, json_mode=True, model_name="gemini-flash-latest")
            test_source = json.loads(res_str).get("test_source", "")
        except Exception as e:
            err_msg = f"Failed initial test generation for {file_path}: {str(e)}"
            logger.error(err_msg)
            aggregated_logs.append(f"--- File: {test_file_name} ---\n{err_msg}\n")
            continue

        if not test_source.strip():
            aggregated_logs.append(f"--- File: {test_file_name} ---\nTest generation returned empty output.\n")
            continue

        # Active feedback, repair, and coverage loop
        current_test_source = test_source
        iterations = 0
        file_passed = 0
        file_failed = 0
        file_coverage = 0.0
        run_log = ""

        # Only execute feedback loop if repo_dir is provided
        if repo_dir:
            initial_run_recorded = False
            
            while iterations < MAX_ITERATIONS:
                iterations += 1
                test_files_payload = [{"file": test_file_name, "source": current_test_source}]
                
                # Execute tests inside temp workspace via Backend TestRunner adapter
                run_res = run_tests_and_measure_coverage(repo_dir, test_files_payload, language)
                file_passed = run_res.get("passed", 0)
                file_failed = run_res.get("failed", 0)
                file_coverage = run_res.get("coverage_percent", 0.0)
                run_log = run_res.get("log", "")
                uncovered_lines = run_res.get("uncovered_lines", [])

                if not initial_run_recorded:
                    test_result["initial_coverage"] = file_coverage
                    initial_run_recorded = True

                # Check execution issues (Syntax / import failures)
                is_compilation_failure = (file_passed == 0 and file_failed > 0 and ("Error" in run_log or "ImportError" in run_log or "SyntaxError" in run_log or "FAIL" in run_log or "failed" in run_log))
                
                if is_compilation_failure:
                    # Repair Loop
                    logger.warning(f"Test suite compilation failure for {test_file_name} on iteration {iterations}. Repairing...")
                    try:
                        repair_prompt = (
                            f"The unit test file '{test_file_name}' you generated failed to run.\n"
                            f"Execution error details:\n{run_log}\n\n"
                            f"Please repair the test file so that it resolves imports and runs successfully under {framework}.\n"
                            f"Original Code under test:\n```\n{source_snippet}\n```\n\n"
                            f"Failed test code:\n```\n{current_test_source}\n```\n\n"
                            f"Return a JSON object with the corrected code under the key 'test_source'."
                        )
                        repair_res = call_gemini(repair_prompt, system_instruction="You are a code fixer. Output ONLY JSON.", json_mode=True)
                        current_test_source = json.loads(repair_res).get("test_source", current_test_source)
                    except Exception as e:
                        logger.error(f"Test repair failed on iteration {iterations}: {str(e)}")
                        break

                elif file_coverage < TARGET_COVERAGE:
                    # Coverage Improvement Loop
                    logger.info(f"Test suite for {test_file_name} coverage is {file_coverage}% (target: {TARGET_COVERAGE}%) on iteration {iterations}. Generating targeted extra tests...")
                    
                    # Extract uncovered code lines for targeted prompt
                    uncovered_snippets = []
                    for lno in uncovered_lines:
                        if 1 <= lno <= len(source_lines):
                            uncovered_snippets.append(f"Line {lno}: {source_lines[lno - 1]}")
                    uncovered_text = "\n".join(uncovered_snippets) if uncovered_snippets else "None specified"

                    try:
                        improve_prompt = (
                            f"The unit test file '{test_file_name}' passed successfully but achieved only {file_coverage}% line coverage.\n"
                            f"Target line coverage: >={TARGET_COVERAGE}% (minimum: >={MIN_COVERAGE}%).\n\n"
                            f"UNCOVERED LINE NUMBERS: {uncovered_lines}\n\n"
                            f"UNCOVERED CODE SNIPPETS:\n{uncovered_text}\n\n"
                            f"Original Target Code:\n```\n{source_snippet}\n```\n\n"
                            f"Current Test Suite Code:\n```\n{current_test_source}\n```\n\n"
                            f"Execution Log:\n{run_log}\n\n"
                            f"Write additional test cases specifically targeting the uncovered lines, branches, and exception paths above.\n"
                            f"Rules:\n"
                            f"- Do NOT remove or break existing passing tests.\n"
                            f"- Ensure all required imports are preserved.\n"
                            f"- Return a JSON object with a single key 'test_source' containing the complete updated test file (existing tests + new targeted tests)."
                        )
                        improve_res = call_gemini(improve_prompt, system_instruction="You are a senior QA engineer optimizing test coverage. Output ONLY JSON.", json_mode=True)
                        current_test_source = json.loads(improve_res).get("test_source", current_test_source)
                    except Exception as e:
                        logger.error(f"Test improvement failed on iteration {iterations}: {str(e)}")
                        break
                else:
                    # Success: coverage >= TARGET_COVERAGE (70%) and tests pass
                    logger.info(f"Test suite for {test_file_name} achieved target coverage: {file_coverage}%")
                    break
            
            test_result["iterations_used"] += iterations
        else:
            run_log = "Tests generated. Subprocess test execution skipped because repo_dir was not provided."

        # Save finalized test source
        test_result["test_files"].append({
            "file": test_file_name,
            "source": current_test_source
        })

        total_passed += file_passed
        total_failed += file_failed
        coverage_sum += file_coverage
        files_tested_count += 1
        aggregated_logs.append(f"--- File: {test_file_name} ---\n{run_log}\n")

    # Aggregate total stats
    test_result["passed"] = total_passed
    test_result["failed"] = total_failed
    test_result["coverage_percent"] = round(coverage_sum / max(1, files_tested_count), 1)
    test_result["log"] = "\n".join(aggregated_logs)

    return test_result


def generate_tests(chunks: list, repo_dir: str = None) -> dict:
    """
    API Entrypoint: Generates unit test suites matching CONTRACT.md §3 TestResult schema.
    """
    return generate_unit_tests(chunks, repo_dir=repo_dir)
