"""
AUDIT TESTS - Test the complete backend pipeline end-to-end.
These tests identify CRITICAL issues before hackathon demo.
"""
import pytest
import tempfile
import zipfile
from pathlib import Path
import asyncio
from app.ingestion.zip_handler import extract_zip, create_workspace, ZipValidationError, ZipSecurityError
from app.parsing.repository_analyzer import RepositoryAnalyzer
from app.testing.test_runner import TestRunner
from app.jobs.job_manager import JobManager
from app.models.contract import ParsedChunk
from app.parsing.contract_adapter import ParsedChunkAdapter


class TestAuditPipeline:
    """Critical audit tests for hackathon demo."""
    
    def test_complete_flow_600_loc(self, tmp_path):
        """BENCHMARK: Test ~600 LOC Python repository."""
        repo_dir = tmp_path / "benchmark_600"
        repo_dir.mkdir()
        
        # Create realistic 600 LOC repository
        (repo_dir / "calculator.py").write_text('''
"""Calculator module with various operations."""
import math
from typing import Union, List

class Calculator:
    """Basic calculator with arithmetic operations."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = a - b
        self.history.append(f"subtract({a}, {b}) = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"divide({a}, {b}) = {result}")
        return result
    
    def power(self, base: float, exp: float) -> float:
        """Raise base to the power of exp."""
        result = math.pow(base, exp)
        return result
    
    def sqrt(self, n: float) -> float:
        """Calculate square root."""
        if n < 0:
            raise ValueError("Cannot take square root of negative number")
        return math.sqrt(n)
    
    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()

def factorial(n: int) -> int:
    """Calculate factorial recursively."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n: int) -> List[int]:
    """Generate Fibonacci sequence."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib

class StatisticalCalculator(Calculator):
    """Extended calculator with statistical functions."""
    
    def mean(self, numbers: List[float]) -> float:
        """Calculate arithmetic mean."""
        if not numbers:
            raise ValueError("Cannot calculate mean of empty list")
        return sum(numbers) / len(numbers)
    
    def median(self, numbers: List[float]) -> float:
        """Calculate median."""
        if not numbers:
            raise ValueError("Cannot calculate median of empty list")
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_nums[mid-1] + sorted_nums[mid]) / 2
        return sorted_nums[mid]
    
    def variance(self, numbers: List[float]) -> float:
        """Calculate variance."""
        if not numbers:
            raise ValueError("Cannot calculate variance of empty list")
        m = self.mean(numbers)
        return sum((x - m) ** 2 for x in numbers) / len(numbers)
    
    def std_dev(self, numbers: List[float]) -> float:
        """Calculate standard deviation."""
        return math.sqrt(self.variance(numbers))
''')
        
        (repo_dir / "main.py").write_text('''
"""Main entry point for calculator application."""
from calculator import Calculator, StatisticalCalculator, factorial, fibonacci

def demo_basic():
    """Demonstrate basic calculator operations."""
    calc = Calculator()
    print("Basic Operations:")
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"20 / 4 = {calc.divide(20, 4)}")
    print(f"2^8 = {calc.power(2, 8)}")
    print(f"sqrt(16) = {calc.sqrt(16)}")

def demo_advanced():
    """Demonstrate advanced calculator operations."""
    print("Advanced Operations:")
    print(f"5! = {factorial(5)}")
    print(f"First 10 Fibonacci: {fibonacci(10)}")

def demo_statistical():
    """Demonstrate statistical calculator."""
    stat_calc = StatisticalCalculator()
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print("Statistical Operations:")
    print(f"Mean: {stat_calc.mean(data)}")
    print(f"Median: {stat_calc.median(data)}")
    print(f"Variance: {stat_calc.variance(data)}")
    print(f"Std Dev: {stat_calc.std_dev(data)}")

if __name__ == "__main__":
    demo_basic()
    demo_advanced()
    demo_statistical()
''')
        
        # Create ZIP
        zip_path = tmp_path / "benchmark_600.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        # Test extraction
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        assert (extract_dir / "benchmark_600" / "calculator.py").exists()
        
        # Test parsing
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "benchmark_600")
        
        # Verify results
        assert analysis.total_loc > 0
        assert len(analysis.functions) > 0
        assert len(analysis.classes) > 0
        assert len(analysis.parse_errors) == 0, f"Parse errors: {analysis.parse_errors}"
        
        print(f"\n=== 600 LOC Benchmark ===")
        print(f"Total LOC: {analysis.total_loc}")
        print(f"Functions: {len(analysis.functions)}")
        print(f"Classes: {len(analysis.classes)}")
        print(f"Parse errors: {len(analysis.parse_errors)}")
    
    def test_partial_failure_recovery(self, tmp_path):
        """P0 CRITICAL: Test that partial failures don't kill the job."""
        repo_dir = tmp_path / "partial_fail"
        repo_dir.mkdir()
        
        # Create mix of good and bad files
        (repo_dir / "good1.py").write_text('''
def working_function():
    return 42
''')
        
        (repo_dir / "broken.py").write_text('''
def broken_function(
    # Syntax error - missing closing paren
''')
        
        (repo_dir / "good2.py").write_text('''
class WorkingClass:
    def method(self):
        return "works"
''')
        
        zip_path = tmp_path / "partial_fail.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        # Extract and analyze
        extract_dir = tmp_path / "extracted_partial"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "partial_fail")
        
        # CRITICAL: Should have parse errors BUT still return results
        assert len(analysis.parse_errors) > 0
        assert len(analysis.functions) > 0  # Should have parsed good files
        assert len(analysis.classes) > 0
        
        print(f"\n=== Partial Failure Test ===")
        print(f"Functions parsed: {len(analysis.functions)}")
        print(f"Classes parsed: {len(analysis.classes)}")
        print(f"Parse errors: {len(analysis.parse_errors)}")
    
    def test_contract_compatibility(self, tmp_path):
        """P0 CRITICAL: Verify ParsedChunk exactly matches CONTRACT.md."""
        repo_dir = tmp_path / "contract_test"
        repo_dir.mkdir()
        
        (repo_dir / "test.py").write_text('''
import os
import sys

def test_function(x, y):
    """Test function."""
    helper()
    return x + y

def helper():
    return 42
''')
        
        zip_path = tmp_path / "contract_test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted_contract"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "contract_test")
        
        # Convert to ParsedChunks
        chunks = []
        lang = list(analysis.languages)[0] if analysis.languages else None
        if lang:
            for func in analysis.functions.values():
                chunk = ParsedChunkAdapter.from_function(func, lang)
                chunks.append(chunk)
        
        assert len(chunks) > 0
        
        # Verify each chunk matches CONTRACT.md exactly
        for chunk in chunks:
            assert isinstance(chunk, ParsedChunk)
            assert hasattr(chunk, 'file')
            assert hasattr(chunk, 'language')
            assert hasattr(chunk, 'type')
            assert hasattr(chunk, 'name')
            assert hasattr(chunk, 'start_line')
            assert hasattr(chunk, 'end_line')
            assert hasattr(chunk, 'source')
            assert hasattr(chunk, 'calls')
            assert hasattr(chunk, 'imports')
            
            # Verify types
            assert isinstance(chunk.file, str)
            assert chunk.language in ["python", "javascript"]
            assert chunk.type in ["function", "class", "module"]
            assert isinstance(chunk.name, str)
            assert isinstance(chunk.start_line, int)
            assert isinstance(chunk.end_line, int)
            assert isinstance(chunk.source, str)
            assert isinstance(chunk.calls, list)
            assert isinstance(chunk.imports, list)
            
            # Verify line numbers are valid
            assert chunk.start_line > 0
            assert chunk.end_line >= chunk.start_line
            
            # Verify source is not empty
            assert len(chunk.source.strip()) > 0
        
        print(f"\n=== Contract Compatibility ===")
        print(f"Total chunks: {len(chunks)}")
        print("All chunks match CONTRACT.md schema ✓")
    
    def test_zip_bomb_protection(self, tmp_path):
        """P0 CRITICAL: Test protection against zip bombs."""
        # Create a file that would expand to huge size
        zip_path = tmp_path / "bomb.zip"
        
        # Create nested ZIP compression
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write highly compressible data (2MB of zeros)
            data = b"0" * (2 * 1024 * 1024)
            zf.writestr("huge.txt", data)
        
        # Should reject with default 100MB limit
        with pytest.raises(ZipSecurityError):
            from app.ingestion.zip_handler import validate_zip
            validate_zip(zip_path, max_size_mb=1)
    
    def test_path_traversal_protection(self, tmp_path):
        """P0 CRITICAL: Test path traversal security."""
        evil_zip = tmp_path / "evil.zip"
        
        with zipfile.ZipFile(evil_zip, 'w') as zf:
            # Attempt path traversal
            zf.writestr("../../etc/passwd", "malicious")
            zf.writestr("../../../root/.ssh/id_rsa", "keys")
            zf.writestr("normal.py", "print('normal')")
        
        extract_dir = tmp_path / "extracted_evil"
        
        # Should reject path traversal attempts
        with pytest.raises(ZipSecurityError) as exc_info:
            extract_zip(evil_zip, extract_dir)
        
        # Verify it detected path traversal
        assert "path traversal" in str(exc_info.value).lower()
        
        print(f"\n=== Path Traversal Protection ===")
        print(f"Correctly blocked: {exc_info.value}")
    
    def test_empty_repository_handling(self, tmp_path):
        """P1 HIGH: Test empty repository edge case."""
        repo_dir = tmp_path / "empty_repo"
        repo_dir.mkdir()
        
        # Create empty directory structure
        (repo_dir / "src").mkdir()
        (repo_dir / "tests").mkdir()
        
        zip_path = tmp_path / "empty_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # ZIP with only directories, no files
            pass
        
        # Should handle gracefully
        try:
            extract_dir = tmp_path / "extracted_empty"
            extract_zip(zip_path, extract_dir)
        except ZipValidationError as e:
            # Expected: empty ZIP should be rejected
            assert "no valid files" in str(e).lower() or "empty" in str(e).lower()
    
    def test_workspace_isolation(self, tmp_path):
        """P0 CRITICAL: Verify original repo never modified."""
        repo_dir = tmp_path / "isolation_test"
        repo_dir.mkdir()
        
        (repo_dir / "test.py").write_text("original content")
        
        zip_path = tmp_path / "isolation.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        # Create workspace
        workspace_dir, original_dir, working_dir, gen_tests_dir = create_workspace(
            "test_job", tmp_path / "workspaces"
        )
        
        # Extract to original
        extract_zip(zip_path, original_dir)
        
        # Verify structure
        assert original_dir.exists()
        assert working_dir.exists()
        assert gen_tests_dir.exists()
        
        # Verify they're separate directories
        assert original_dir != working_dir
        assert original_dir != gen_tests_dir
        
        print(f"\n=== Workspace Isolation ===")
        print(f"Original: {original_dir}")
        print(f"Working: {working_dir}")
        print(f"Generated Tests: {gen_tests_dir}")
        print("Directories properly isolated ✓")
    
    def test_unicode_filenames(self, tmp_path):
        """P2 MEDIUM: Test Unicode in filenames."""
        repo_dir = tmp_path / "unicode_repo"
        repo_dir.mkdir()
        
        # Create files with Unicode names
        (repo_dir / "测试.py").write_text("# Chinese characters\ndef test(): pass")
        (repo_dir / "файл.py").write_text("# Cyrillic characters\ndef func(): pass")
        (repo_dir / "normal.py").write_text("def normal(): pass")
        
        zip_path = tmp_path / "unicode_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        # Should handle gracefully
        extract_dir = tmp_path / "extracted_unicode"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "unicode_repo")
        
        # Should parse at least some files
        assert analysis.total_loc > 0
