import pytest
import os
import json
from unittest.mock import patch, MagicMock
from google.api_core.exceptions import ResourceExhausted

from backend.app.ai import gemini_client
from backend.app.ai.gemini_client import call_gemini, telemetry
from backend.app.ai.explainer import generate_explanations
from backend.app.ai.test_gen import generate_unit_tests
from backend.app.ai.refactor import (
    generate_refactored_code, 
    get_python_signatures, 
    get_js_signatures, 
    compare_signatures
)

# Set API key for testing so it doesn't fail configure checks
os.environ["GEMINI_API_KEY"] = "mock_api_key_for_testing"
gemini_client._configured = True


# =====================================================================
# 1. GEMINI CLIENT TESTS
# =====================================================================
@patch("google.generativeai.GenerativeModel")
def test_gemini_client_success(mock_model_class):
    telemetry.reset()
    
    # Configure mock model instance
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello, world!"
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    response_text = call_gemini("Test prompt")
    
    assert response_text == "Hello, world!"
    assert telemetry.total_calls == 1
    assert telemetry.successful_calls == 1
    assert telemetry.failed_calls == 0
    assert telemetry.retries == 0


@patch("google.generativeai.GenerativeModel")
def test_gemini_client_retry_and_success(mock_model_class):
    telemetry.reset()
    
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Success after rate limit!"
    
    # First call raises ResourceExhausted, second call succeeds
    mock_model.generate_content.side_effect = [
        ResourceExhausted("Rate limit exceeded"),
        mock_response
    ]
    mock_model_class.return_value = mock_model

    # Use a patch on time.sleep to run quickly without delaying tests
    with patch("time.sleep") as mock_sleep:
        response_text = call_gemini("Test retry prompt")
        
        assert response_text == "Success after rate limit!"
        assert telemetry.total_calls == 1
        assert telemetry.successful_calls == 1
        assert telemetry.retries == 1
        assert telemetry.failed_calls == 0
        mock_sleep.assert_called_once()


@patch("google.generativeai.GenerativeModel")
def test_gemini_client_exhaustion(mock_model_class):
    telemetry.reset()
    
    mock_model = MagicMock()
    # Always raise ResourceExhausted
    mock_model.generate_content.side_effect = ResourceExhausted("Rate limit exceeded")
    mock_model_class.return_value = mock_model

    with patch("time.sleep") as mock_sleep, pytest.raises(Exception) as exc_info:
        call_gemini("Test failing prompt")
        
    assert "Gemini API call failed" in str(exc_info.value)
    assert telemetry.total_calls == 1
    assert telemetry.failed_calls == 1
    assert telemetry.retries >= 3  # At least 3 attempts per candidate model
    assert telemetry.successful_calls == 0


# =====================================================================
# 2. EXPLANATION ENGINE TESTS
# =====================================================================
@patch("backend.app.ai.explainer.call_gemini")
def test_explanation_engine_structure(mock_call_gemini):
    # Mock calls to return repo overview, module overview, and function JSON
    mock_call_gemini.side_effect = [
        "This repository provides mathematical helper functions.", # Repository Overview
        "This file provides math helpers.",  # Module overview
        '{"functions": [{"name": "add", "purpose": "Adds two numbers", "inputs": ["a", "b"], "outputs": "sum", "logic": ["return a+b"], "dependencies": [], "side_effects": ["none"], "potential_risks": ["none"]}]}'  # Function JSON
    ]

    mock_chunks = [
        {
            "file": "math_utils.py",
            "language": "python",
            "type": "module",
            "name": "math_utils.py",
            "start_line": 1,
            "end_line": 20,
            "source": "def add(a, b): return a + b",
            "imports": [],
            "calls": []
        },
        {
            "file": "math_utils.py",
            "language": "python",
            "type": "function",
            "name": "add",
            "start_line": 5,
            "end_line": 10,
            "source": "def add(a, b): return a + b",
            "imports": [],
            "calls": []
        }
    ]

    result = generate_explanations(mock_chunks)

    # 1. Assert keys in result
    assert "modules" in result
    assert "functions" in result

    # 2. Check Repository Overview entry is present
    repo_overview = next((m for m in result["modules"] if m["file"] == "Repository Summary"), None)
    assert repo_overview is not None

    # 3. Check specific file module summary
    file_summary = next((m for m in result["modules"] if m["file"] == "math_utils.py"), None)
    assert file_summary is not None
    assert file_summary["summary"] == "This file provides math helpers."

    # 4. Check function detail parsing and formatting
    assert len(result["functions"]) == 1
    func_entry = result["functions"][0]
    assert func_entry["name"] == "add"
    assert func_entry["file"] == "math_utils.py"
    assert "**Purpose:** Adds two numbers" in func_entry["summary"]
    assert "**Logic Steps:**\n- return a+b" in func_entry["summary"]
    assert "**Potential Risks:**\n- none" in func_entry["summary"]


# =====================================================================
# 3. TEST GENERATOR TESTS (COVERAGE LOOP)
# =====================================================================
@patch("backend.app.ai.test_gen.call_gemini")
@patch("backend.app.ai.test_gen.run_tests_and_measure_coverage")
def test_test_generation_feedback_loop_success(mock_run_tests, mock_call_gemini):
    # Initial code generation mock
    mock_call_gemini.side_effect = [
        '{"test_source": "def test_add(): assert add(1, 2) == 3"}'
    ]
    
    # Mock test runner to return 75% coverage (above 70% target, so loops exit immediately)
    mock_run_tests.return_value = {
        "passed": 1,
        "failed": 0,
        "coverage_percent": 75.0,
        "log": "pytest successful"
    }

    mock_chunks = [
        {
            "file": "utils.py",
            "language": "python",
            "type": "module",
            "name": "utils.py",
            "start_line": 1,
            "end_line": 10,
            "source": "def add(x, y): return x + y",
            "imports": [],
            "calls": []
        }
    ]

    result = generate_unit_tests(mock_chunks, repo_dir="mock_repo_dir")

    assert len(result["test_files"]) == 1
    assert result["test_files"][0]["file"] == "test_utils.py"
    assert result["test_files"][0]["source"] == "def test_add(): assert add(1, 2) == 3"
    assert result["coverage_percent"] == 75.0
    assert result["passed"] == 1
    assert result["failed"] == 0
    assert result["iterations_used"] == 1


@patch("backend.app.ai.test_gen.call_gemini")
@patch("backend.app.ai.test_gen.run_tests_and_measure_coverage")
def test_test_generation_repair_and_improvement_loop(mock_run_tests, mock_call_gemini):
    # Call 1: Initial test generation
    # Call 2: Repair prompt (after syntax error)
    mock_call_gemini.side_effect = [
        '{"test_source": "def test_add(): invalid_syntax"}',
        '{"test_source": "def test_add(): assert add(1, 2) == 3"}'
    ]
    
    # Run 1: Returns compilation error (0 passed, 1 failed, 0% coverage)
    # Run 2: Returns 72% coverage (success)
    mock_run_tests.side_effect = [
        {"passed": 0, "failed": 1, "coverage_percent": 0.0, "log": "SyntaxError: invalid syntax"},
        {"passed": 1, "failed": 0, "coverage_percent": 72.0, "log": "pytest successful"}
    ]

    mock_chunks = [
        {
            "file": "utils.py",
            "language": "python",
            "type": "module",
            "name": "utils.py",
            "start_line": 1,
            "end_line": 10,
            "source": "def add(x, y): return x + y",
            "imports": [],
            "calls": []
        }
    ]

    # Run generator with a mockup directory path to enable runner execution
    result = generate_unit_tests(mock_chunks, repo_dir="mock_repo_dir")

    assert len(result["test_files"]) == 1
    assert result["coverage_percent"] == 72.0
    assert result["passed"] == 1
    assert result["failed"] == 0
    assert result["iterations_used"] == 2  # Used 2 runs to repair the tests
    assert result["initial_coverage"] == 0.0


# =====================================================================
# 4. REFACTORING & BREAKING CHANGE TESTS
# =====================================================================
def test_ast_python_signature_extraction():
    original_code = (
        "def add(a, b=5):\n"
        "    return a + b\n\n"
        "class Helper:\n"
        "    def run(self, action, timeout=10):\n"
        "        pass\n"
    )
    
    signatures = get_python_signatures(original_code)
    
    assert "add" in signatures
    assert signatures["add"]["args"] == [
        {"name": "a", "has_default": False},
        {"name": "b", "has_default": True}
    ]
    
    assert "Helper.run" in signatures
    assert signatures["Helper.run"]["args"] == [
        {"name": "self", "has_default": False},
        {"name": "action", "has_default": False},
        {"name": "timeout", "has_default": True}
    ]


def test_ast_signature_comparison_breaking_changes():
    # 1. Parameter Removed
    orig = {"foo": {"args": [{"name": "x", "has_default": False}, {"name": "y", "has_default": False}]}}
    refact = {"foo": {"args": [{"name": "x", "has_default": False}]}}
    warnings = compare_signatures(orig, refact)
    assert any("Parameter 'y' was removed" in w for w in warnings)

    # 2. Required Parameter Added
    orig = {"foo": {"args": [{"name": "x", "has_default": False}]}}
    refact = {"foo": {"args": [{"name": "x", "has_default": False}, {"name": "y", "has_default": False}]}}
    warnings = compare_signatures(orig, refact)
    assert any("Required parameter 'y' was added" in w for w in warnings)

    # 3. Parameter Order Changed
    orig = {"foo": {"args": [{"name": "x", "has_default": False}, {"name": "y", "has_default": False}]}}
    refact = {"foo": {"args": [{"name": "y", "has_default": False}, {"name": "x", "has_default": False}]}}
    warnings = compare_signatures(orig, refact)
    assert any("Parameter order of function 'foo' was changed" in w for w in warnings)

    # 4. Function Removed
    orig = {"foo": {"args": []}}
    refact = {}
    warnings = compare_signatures(orig, refact)
    assert any("Function/Method 'foo' was removed" in w for w in warnings)
