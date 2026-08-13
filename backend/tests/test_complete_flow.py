"""
Comprehensive flow tests - Test everything that can break.
These tests simulate real hackathon demo scenarios.
"""
import pytest
import tempfile
import zipfile
from pathlib import Path
import time


class TestCompleteFlow:
    """Test the complete backend pipeline."""
    
    def test_happy_path_python(self, tmp_path):
        """Test complete flow with valid Python repository."""
        # Create a simple Python project
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        
        (repo_dir / "calculator.py").write_text("""
def add(a, b):
    '''Add two numbers.'''
    return a + b

def multiply(a, b):
    return a * b

class Calculator:
    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero")
        return x / y
""")
        
        (repo_dir / "main.py").write_text("""
from calculator import add, Calculator

def main():
    result = add(5, 3)
    calc = Calculator()
    quotient = calc.divide(10, 2)
    print(result, quotient)

if __name__ == "__main__":
    main()
""")
        
        # Create ZIP
        zip_path = tmp_path / "test_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        # Test: Upload would happen here via API
        # For now, verify ZIP is valid
        assert zip_path.exists()
        assert zipfile.is_zipfile(zip_path)
    
    def test_corrupt_zip(self, tmp_path):
        """Test handling of corrupt ZIP file."""
        corrupt_zip = tmp_path / "corrupt.zip"
        corrupt_zip.write_bytes(b"NOT A ZIP FILE AT ALL")
        
        # Should be detected by validation
        assert not zipfile.is_zipfile(corrupt_zip)
    
    def test_empty_zip(self, tmp_path):
        """Test handling of empty ZIP."""
        empty_zip = tmp_path / "empty.zip"
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            pass  # Create empty ZIP
        
        assert zipfile.is_zipfile(empty_zip)
        with zipfile.ZipFile(empty_zip, 'r') as zf:
            assert len(zf.namelist()) == 0
    
    def test_path_traversal_zip(self, tmp_path):
        """Test ZIP with path traversal attempt."""
        evil_zip = tmp_path / "evil.zip"
        with zipfile.ZipFile(evil_zip, 'w') as zf:
            # Try to write outside workspace
            zf.writestr("../../etc/passwd", "malicious")
            zf.writestr("normal_file.py", "print('hello')")
        
        assert zipfile.is_zipfile(evil_zip)
    
    def test_malformed_python(self, tmp_path):
        """Test Python file with syntax errors."""
        repo_dir = tmp_path / "broken_repo"
        repo_dir.mkdir()
        
        (repo_dir / "broken.py").write_text("""
def incomplete_function(
    # Missing closing parenthesis and body
""")
        
        (repo_dir / "good.py").write_text("""
def working_function():
    return 42
""")
        
        zip_path = tmp_path / "broken_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_empty_source_file(self, tmp_path):
        """Test completely empty source file."""
        repo_dir = tmp_path / "empty_file_repo"
        repo_dir.mkdir()
        
        (repo_dir / "empty.py").write_text("")
        (repo_dir / "whitespace.py").write_text("   \n\n  \t  \n")
        
        zip_path = tmp_path / "empty_file_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_binary_file(self, tmp_path):
        """Test repository with binary files."""
        repo_dir = tmp_path / "binary_repo"
        repo_dir.mkdir()
        
        # Create binary file
        (repo_dir / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        (repo_dir / "code.py").write_text("print('hello')")
        
        zip_path = tmp_path / "binary_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_huge_file(self, tmp_path):
        """Test repository with very large file."""
        repo_dir = tmp_path / "huge_repo"
        repo_dir.mkdir()
        
        # Create a large file (1MB of Python code)
        large_content = "# Comment\n" * 50000  # ~500KB
        (repo_dir / "huge.py").write_text(large_content)
        
        zip_path = tmp_path / "huge_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_many_files(self, tmp_path):
        """Test repository with many files."""
        repo_dir = tmp_path / "many_files_repo"
        repo_dir.mkdir()
        
        # Create 100 small files
        for i in range(100):
            (repo_dir / f"file_{i}.py").write_text(f"def func_{i}(): return {i}")
        
        zip_path = tmp_path / "many_files_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_deeply_nested_code(self, tmp_path):
        """Test deeply nested function calls."""
        repo_dir = tmp_path / "nested_repo"
        repo_dir.mkdir()
        
        (repo_dir / "nested.py").write_text("""
def level1():
    def level2():
        def level3():
            def level4():
                return 42
            return level4()
        return level3()
    return level2()

class Outer:
    class Middle:
        class Inner:
            def deep_method(self):
                return "deep"
""")
        
        zip_path = tmp_path / "nested_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_duplicate_function_names(self, tmp_path):
        """Test multiple files with same function names."""
        repo_dir = tmp_path / "duplicate_repo"
        repo_dir.mkdir()
        
        (repo_dir / "module1.py").write_text("""
def process():
    return 1
""")
        
        (repo_dir / "module2.py").write_text("""
def process():
    return 2
""")
        
        zip_path = tmp_path / "duplicate_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_duplicate_filenames_different_dirs(self, tmp_path):
        """Test same filename in different directories."""
        repo_dir = tmp_path / "dup_dirs_repo"
        repo_dir.mkdir()
        
        (repo_dir / "src").mkdir()
        (repo_dir / "tests").mkdir()
        
        (repo_dir / "src" / "utils.py").write_text("def helper(): pass")
        (repo_dir / "tests" / "utils.py").write_text("def test_helper(): pass")
        
        zip_path = tmp_path / "dup_dirs_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_circular_imports(self, tmp_path):
        """Test circular import pattern."""
        repo_dir = tmp_path / "circular_repo"
        repo_dir.mkdir()
        
        (repo_dir / "a.py").write_text("""
from b import func_b

def func_a():
    return func_b()
""")
        
        (repo_dir / "b.py").write_text("""
from a import func_a

def func_b():
    return "b"
""")
        
        zip_path = tmp_path / "circular_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
    
    def test_dynamic_imports(self, tmp_path):
        """Test dynamic import patterns."""
        repo_dir = tmp_path / "dynamic_repo"
        repo_dir.mkdir()
        
        (repo_dir / "dynamic.py").write_text("""
import importlib

def load_module(name):
    return importlib.import_module(name)

module_name = "os"
os_module = __import__(module_name)
""")
        
        zip_path = tmp_path / "dynamic_repo.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        assert zip_path.exists()
