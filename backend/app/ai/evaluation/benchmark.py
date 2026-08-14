import os
import sys
import json
import shutil
import tempfile
import logging
from datetime import datetime

# Add root folder to python path to resolve absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from backend.app.ai.gemini_client import call_gemini, telemetry
from backend.app.ai.explainer import generate_explanations
from backend.app.ai.test_gen import generate_unit_tests
from backend.app.ai.refactor import generate_refactored_code
from backend.app.ai.adapters.parser_adapter import parse_python_source_to_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codeoracle.benchmark")

BENCHMARK_RESULTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "results.json"))

# Predefined benchmark snippets and expected reference facts
SNIPPET_CALCULATOR = {
    "name": "calculator.py",
    "language": "python",
    "source": (
        "def divide(a, b):\n"
        "    \"\"\"\n"
        "    Divides parameter a by parameter b.\n"
        "    Raises ValueError if denominator b is zero.\n"
        "    \"\"\"\n"
        "    if b == 0:\n"
        "        raise ValueError(\"Denominator cannot be zero.\")\n"
        "    return a / b\n"
    ),
    "expected_facts": {
        "purpose": "Divide number a by number b.",
        "inputs": ["a (numerator)", "b (denominator)"],
        "outputs": "Quotient result of a / b",
        "dependencies": "None",
        "side_effects": "None",
        "risks": "ValueError raised if parameter b is 0 (division by zero)."
    }
}

SNIPPET_BANK = {
    "name": "bank.py",
    "language": "python",
    "source": (
        "class BankAccount:\n"
        "    def __init__(self, balance: float):\n"
        "        self.balance = balance\n\n"
        "    def deposit(self, amount: float) -> float:\n"
        "        if amount <= 0:\n"
        "            raise ValueError(\"Deposit amount must be positive.\")\n"
        "        self.balance += amount\n"
        "        return self.balance\n"
    ),
    "expected_facts": {
        "purpose": "Manage deposits and balances for bank accounts.",
        "inputs": ["balance in constructor", "amount in deposit method"],
        "outputs": "Updated account balance (float)",
        "dependencies": "None",
        "side_effects": "Modifies internal account state (self.balance)",
        "risks": "ValueError if a negative deposit amount is passed."
    }
}

def evaluate_explanation_with_llm(generated_summary: str, expected_facts: dict) -> dict:
    """
    Uses Gemini as an evaluator (LLM-as-a-judge) to grade explanations
    against expected fact sheets on Accuracy, Completeness, and Clarity.
    Grades on a 1-5 scale (1=Poor, 5=Excellent).
    """
    grading_prompt = (
        f"You are a Quality Assurance grading bot. Evaluate the quality of a generated code explanation against a predefined set of reference facts.\n\n"
        f"Predefined Reference Facts:\n{json.dumps(expected_facts, indent=2)}\n\n"
        f"Generated Explanation:\n{generated_summary}\n\n"
        f"Grade on a scale from 1 (Poor) to 5 (Excellent) for the following three categories:\n"
        f"1. Accuracy: Are the claims in the generated explanation factually correct based on the reference facts? (No hallucinations or incorrect assumptions)\n"
        f"2. Completeness: Did the generated explanation cover all key details mentioned in the reference facts (inputs, outputs, side effects, risks)?\n"
        f"3. Clarity: Is the explanation written in a clear, easy-to-read, and professional manner?\n\n"
        f"Return a JSON object containing your grades and brief justifications:\n"
        f'{{\n'
        f'  "accuracy": 5,\n'
        f'  "completeness": 4,\n'
        f'  "clarity": 5,\n'
        f'  "justification": "Explanation here..."\n'
        f'}}'
    )
    
    try:
        sys_instruction = "You are a factual grader. Output ONLY valid JSON."
        grading_res = call_gemini(grading_prompt, system_instruction=sys_instruction, json_mode=True, model_name="gemini-flash-latest")
        return json.loads(grading_res)
    except Exception as e:
        logger.error(f"Failed LLM evaluation call: {str(e)}")
        return {"accuracy": 1, "completeness": 1, "clarity": 1, "justification": f"Failed evaluation: {str(e)}"}

def run_benchmark():
    logger.info("Initializing CodeOracle AI benchmark run...")
    
    # Reset telemetry
    telemetry.reset()
    
    snippets = [SNIPPET_CALCULATOR, SNIPPET_BANK]
    benchmark_reports = []
    
    # Create isolated temp workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = os.path.join(temp_dir, "repo")
        os.makedirs(repo_dir)
        
        for idx, snippet in enumerate(snippets):
            name = snippet["name"]
            source = snippet["source"]
            language = snippet["language"]
            expected_facts = snippet["expected_facts"]
            
            logger.info(f"Evaluating snippet {idx+1}/{len(snippets)}: {name}...")
            
            # Write source snippet to temp workspace
            file_path = os.path.join(repo_dir, name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(source)
                
            # Parse source file
            chunks = parse_python_source_to_chunks(name, source)
            
            # 1. Evaluate Explanations
            explanations = generate_explanations(chunks)
            func_exp = next((f for f in explanations["functions"] if f["file"] == name), None)
            
            exp_grades = {"accuracy": 1, "completeness": 1, "clarity": 1, "justification": "No explanations generated."}
            if func_exp:
                exp_grades = evaluate_explanation_with_llm(func_exp["summary"], expected_facts)
                
            # 2. Evaluate Test Generation and Coverage Loop
            test_results = generate_unit_tests(chunks, repo_dir)
            coverage = test_results.get("coverage_percent", 0.0)
            tests_passed = test_results.get("passed", 0)
            tests_failed = test_results.get("failed", 0)
            iterations_used = test_results.get("iterations_used", 0)
            
            # 3. Evaluate Refactoring and Breaking Change Detection
            refactor_results = generate_refactored_code(chunks, repo_dir)
            refact_file_res = next((f for f in refactor_results["files"] if f["original_file"] == name), None)
            
            refact_syntax_valid = False
            breaking_changes_detected = []
            if refact_file_res:
                refact_source = refact_file_res["refactored_source"]
                warnings = refact_file_res["breaking_changes"]
                breaking_changes_detected = [w for w in warnings if "VALIDATION FAILED" not in w]
                
                # Verify syntax
                try:
                    import ast
                    ast.parse(refact_source)
                    refact_syntax_valid = True
                except SyntaxError:
                    refact_syntax_valid = False

            # Compile snippet report
            report = {
                "name": name,
                "explanation_evaluation": exp_grades,
                "test_evaluation": {
                    "coverage_percent": coverage,
                    "passed": tests_passed,
                    "failed": tests_failed,
                    "iterations_used": iterations_used,
                    "target_coverage_met": coverage >= 70.0,
                    "minimum_coverage_met": coverage > 60.0
                },
                "refactor_evaluation": {
                    "syntax_valid": refact_syntax_valid,
                    "breaking_changes_detected": breaking_changes_detected
                }
            }
            benchmark_reports.append(report)

    # Calculate overall average scores
    avg_accuracy = sum(r["explanation_evaluation"]["accuracy"] for r in benchmark_reports) / len(benchmark_reports)
    avg_completeness = sum(r["explanation_evaluation"]["completeness"] for r in benchmark_reports) / len(benchmark_reports)
    avg_clarity = sum(r["explanation_evaluation"]["clarity"] for r in benchmark_reports) / len(benchmark_reports)
    overall_exp_score = round((avg_accuracy + avg_completeness + avg_clarity) / 3.0, 2)

    avg_coverage = sum(r["test_evaluation"]["coverage_percent"] for r in benchmark_reports) / len(benchmark_reports)

    # Save benchmark report to results.json
    final_output = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "telemetry": telemetry.to_dict(),
        "summary": {
            "average_explanation_score": overall_exp_score,
            "explanation_accuracy": round(avg_accuracy, 2),
            "explanation_completeness": round(avg_completeness, 2),
            "explanation_clarity": round(avg_clarity, 2),
            "average_test_coverage_percent": round(avg_coverage, 1)
        },
        "details": benchmark_reports
    }
    
    os.makedirs(os.path.dirname(BENCHMARK_RESULTS_FILE), exist_ok=True)
    with open(BENCHMARK_RESULTS_FILE, "w", encoding="utf-8") as rf:
        json.dump(final_output, rf, indent=2)
        
    logger.info(f"AI benchmark run completed! Results saved to {BENCHMARK_RESULTS_FILE}")
    logger.info(f"Explanations score: {overall_exp_score}/5.0 (Target: >=4/5)")
    logger.info(f"Average Test Coverage: {avg_coverage}% (Target: 70-80%)")

if __name__ == "__main__":
    # Ensure environment key is configured before execution
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is not set. Please set it in your .env file or environment.")
        sys.exit(1)
    run_benchmark()
