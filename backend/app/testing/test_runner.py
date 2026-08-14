"""Test execution and coverage measurement."""
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
@dataclass
class TestRunResult:
    """Result from test execution."""

    __test__ = False

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    coverage_percent: float = 0.0
    timeout: bool = False
    
    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped + self.errors
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timeout


class TestRunner:
    """
    Execute generated tests in isolated environment.
    Never execute in the original repository.
    """

    __test__ = False

    def __init__(self, timeout_seconds: int = 300):
        ...
    
    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize test runner.
        
        Args:
            timeout_seconds: Maximum execution time
        """
        self.timeout_seconds = timeout_seconds
    
    def run_python_tests(
        self,
        test_directory: Path,
        source_directory: Optional[Path] = None,
        measure_coverage: bool = True
    ) -> TestRunResult:
        """
        Run Python tests using pytest.
        
        Args:
            test_directory: Directory containing test files
            source_directory: Directory containing source code (for coverage)
            measure_coverage: Whether to measure coverage
            
        Returns:
            TestRunResult
        """
        result = TestRunResult()
        
        if not test_directory.exists():
            result.stderr = "Test directory does not exist"
            result.exit_code = 1
            return result
        
        # Build pytest command
        cmd = ["pytest", str(test_directory), "-v"]
        
        if measure_coverage and source_directory:
            cmd.extend([
                f"--cov={source_directory}",
                "--cov-report=term-missing",
                "--cov-report=json"
            ])
        
        try:
            # Run with timeout
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=test_directory.parent
            )
            
            result.exit_code = process.returncode
            result.stdout = process.stdout
            result.stderr = process.stderr
            
            # Parse pytest output
            self._parse_pytest_output(process.stdout, result)
            
            # Parse coverage if available
            if measure_coverage and source_directory:
                coverage_file = test_directory.parent / "coverage.json"
                if coverage_file.exists():
                    result.coverage_percent = self._parse_coverage_json(coverage_file)
            
        except subprocess.TimeoutExpired:
            result.timeout = True
            result.stderr = f"Test execution timeout after {self.timeout_seconds}s"
            result.exit_code = -1
        
        except FileNotFoundError:
            result.stderr = "pytest not found. Install: pip install pytest pytest-cov"
            result.exit_code = 1
        
        except Exception as e:
            result.stderr = f"Test execution error: {e}"
            result.exit_code = 1
        
        return result
    
    def run_javascript_tests(
        self,
        test_directory: Path,
        package_json_dir: Optional[Path] = None
    ) -> TestRunResult:
        """
        Run JavaScript tests.
        Attempts to use the repository's test runner.
        
        Args:
            test_directory: Directory containing test files
            package_json_dir: Directory containing package.json
            
        Returns:
            TestRunResult
        """
        result = TestRunResult()
        
        if not test_directory.exists():
            result.stderr = "Test directory does not exist"
            result.exit_code = 1
            return result
        
        # Try to find test command
        if package_json_dir and (package_json_dir / "package.json").exists():
            # Use npm test
            cmd = ["npm", "test"]
            cwd = package_json_dir
        else:
            result.stderr = "No package.json found for JavaScript tests"
            result.exit_code = 1
            return result
        
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=cwd
            )
            
            result.exit_code = process.returncode
            result.stdout = process.stdout
            result.stderr = process.stderr
            
            # Basic parsing - framework-specific parsing would be more complex
            if "pass" in process.stdout.lower():
                result.passed = process.stdout.lower().count("pass")
            if "fail" in process.stdout.lower():
                result.failed = process.stdout.lower().count("fail")
            
        except subprocess.TimeoutExpired:
            result.timeout = True
            result.stderr = f"Test execution timeout after {self.timeout_seconds}s"
            result.exit_code = -1
        
        except FileNotFoundError:
            result.stderr = "npm not found"
            result.exit_code = 1
        
        except Exception as e:
            result.stderr = f"Test execution error: {e}"
            result.exit_code = 1
        
        return result
    
    def validate_test_syntax(
        self,
        test_file: Path,
        language: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate test file syntax before execution.
        
        Args:
            test_file: Path to test file
            language: 'python' or 'javascript'
            
        Returns:
            (is_valid, error_message)
        """
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                source = f.read()
            
            if language == 'python':
                import ast
                try:
                    ast.parse(source)
                    return True, None
                except SyntaxError as e:
                    return False, f"Syntax error: {e}"
            
            elif language == 'javascript':
                # Basic validation - could use acorn or similar for JS
                if not source.strip():
                    return False, "Empty test file"
                return True, None
            
            else:
                return False, f"Unsupported language: {language}"
        
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def _parse_pytest_output(self, output: str, result: TestRunResult):
        """Parse pytest output to extract test counts."""
        lines = output.splitlines()
        
        for line in lines:
            line_lower = line.lower()
            
            # Look for summary line like "5 passed, 2 failed in 1.23s"
            if " passed" in line_lower or " failed" in line_lower:
                parts = line.split()
                for i, part in enumerate(parts):
                    if i > 0:
                        try:
                            count = int(parts[i-1])
                            if "passed" in part:
                                result.passed = count
                            elif "failed" in part:
                                result.failed = count
                            elif "skipped" in part:
                                result.skipped = count
                            elif "error" in part:
                                result.errors = count
                        except (ValueError, IndexError):
                            pass
    
    def _parse_coverage_json(self, coverage_file: Path) -> float:
        """Parse coverage.json to get line coverage percentage."""
        try:
            import json
            with open(coverage_file, 'r') as f:
                data = json.load(f)
            
            # coverage.json format has totals
            totals = data.get('totals', {})
            percent_covered = totals.get('percent_covered', 0.0)
            
            return round(percent_covered, 2)
        
        except Exception:
            return 0.0
    
    def create_test_workspace(
        self,
        source_dir: Path,
        test_files: Dict[str, str]
    ) -> Path:
        """
        Create isolated workspace for test execution.
        
        Args:
            source_dir: Original source directory
            test_files: Dict mapping test file names to content
            
        Returns:
            Path to test workspace
        """
        # Create temporary workspace
        temp_dir = Path(tempfile.mkdtemp(prefix="codeoracle_test_"))
        
        # Copy source files
        source_copy = temp_dir / "src"
        shutil.copytree(source_dir, source_copy)
        
        # Write test files
        test_dir = temp_dir / "tests"
        test_dir.mkdir()
        
        for filename, content in test_files.items():
            test_file = test_dir / filename
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return temp_dir
    
    def cleanup_test_workspace(self, workspace: Path):
        """Clean up test workspace."""
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
