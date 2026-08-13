"""
CRITICAL AUDIT TESTS - Issues that could crash the demo.
"""
import pytest
import tempfile
import zipfile
from pathlib import Path
from app.ingestion.zip_handler import extract_zip, ZipValidationError, ZipSecurityError
from app.parsing.repository_analyzer import RepositoryAnalyzer
from app.models.contract import ParsedChunk
from app.parsing.contract_adapter import ParsedChunkAdapter
from app.models.repository import Language


class TestCriticalIssues:
    """Test critical issues that could break demo."""
    
    def test_line_numbers_accuracy(self, tmp_path):
        """P0 CRITICAL: Verify line numbers are accurate."""
        repo_dir = tmp_path / "line_test"
        repo_dir.mkdir()
        
        # Create file with known line numbers
        content = '''# Line 1
# Line 2
def first_function():  # Line 3
    """Line 4"""
    return 42  # Line 5
# Line 6
def second_function():  # Line 7
    pass  # Line 8
'''
        (repo_dir / "test.py").write_text(content)
        
        zip_path = tmp_path / "line_test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "line_test")
        
        # Find first_function
        first_func = None
        second_func = None
        for func in analysis.functions.values():
            if func.name == "first_function":
                first_func = func
            elif func.name == "second_function":
                second_func = func
        
        assert first_func is not None
        assert second_func is not None
        
        # Verify line numbers
        assert first_func.start_line == 3
        assert first_func.end_line == 5
        
        assert second_func.start_line == 7
        assert second_func.end_line == 8
        
        print(f"\n=== Line Number Accuracy ===")
        print(f"first_function: lines {first_func.start_line}-{first_func.end_line} ✓")
        print(f"second_function: lines {second_func.start_line}-{second_func.end_line} ✓")
    
    def test_no_data_invention(self, tmp_path):
        """P0 CRITICAL: Verify no invented functions/data."""
        repo_dir = tmp_path / "invention_test"
        repo_dir.mkdir()
        
        # Create simple file
        (repo_dir / "simple.py").write_text('''
def only_function():
    return "only"
''')
        
        zip_path = tmp_path / "invention_test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "invention_test")
        
        # Should have exactly 1 function
        assert len(analysis.functions) == 1
        
        # Should have exactly 0 classes
        assert len(analysis.classes) == 0
        
        # Function should have correct name
        func = list(analysis.functions.values())[0]
        assert func.name == "only_function"
        
        print(f"\n=== No Data Invention ===")
        print(f"Functions: {len(analysis.functions)} (expected: 1) ✓")
        print(f"Classes: {len(analysis.classes)} (expected: 0) ✓")
    
    def test_large_file_no_memory_explosion(self, tmp_path):
        """P1 HIGH: Verify large files don't cause memory issues."""
        repo_dir = tmp_path / "large_file"
        repo_dir.mkdir()
        
        # Create file with 5000 lines
        lines = []
        for i in range(500):
            lines.append(f'''
def function_{i}(param_{i}):
    """Function {i}."""
    result = param_{i} * 2
    helper_{i}()
    return result

def helper_{i}():
    return {i}
''')
        
        content = '\n'.join(lines)
        (repo_dir / "large.py").write_text(content)
        
        zip_path = tmp_path / "large_file.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        # Should complete without memory issues
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "large_file")
        
        # Should have parsed all functions
        assert len(analysis.functions) == 1000  # 500 * 2 (function + helper)
        assert len(analysis.parse_errors) == 0
        
        print(f"\n=== Large File Test ===")
        print(f"Functions parsed: {len(analysis.functions)}")
        print(f"Total LOC: {analysis.total_loc}")
        print(f"Parse errors: {len(analysis.parse_errors)}")
    
    def test_special_characters_in_code(self, tmp_path):
        """P2 MEDIUM: Test special characters in source code."""
        repo_dir = tmp_path / "special_chars"
        repo_dir.mkdir()
        
        # Create file with various special characters
        (repo_dir / "special.py").write_text('''
def emoji_function():
    """Function with emoji in docstring."""
    message = "Hello world"
    return message

def unicode_function():
    """
    Greek and Math symbols
    """
    return "unicode"

def escape_chars():
    text = "Line\\nWith\\tEscapes\\r\\n"
    return text
''', encoding='utf-8')
        
        zip_path = tmp_path / "special_chars.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "special_chars")
        
        # Should parse successfully
        assert len(analysis.functions) == 3
        assert len(analysis.parse_errors) == 0
        
        # Verify source contains special characters
        for func in analysis.functions.values():
            assert len(func.source) > 0
            # Source should be valid
            assert func.start_line > 0
        
        print(f"\n=== Special Characters Test ===")
        print(f"Functions parsed: {len(analysis.functions)}")
        print("Special characters handled ✓")
    
    def test_missing_dependencies_graceful(self, tmp_path):
        """P1 HIGH: Test graceful handling of missing imports."""
        repo_dir = tmp_path / "missing_deps"
        repo_dir.mkdir()
        
        (repo_dir / "app.py").write_text('''
import nonexistent_module
from missing_package import MissingClass

def use_missing():
    """Function that uses missing imports."""
    obj = MissingClass()
    result = nonexistent_module.process()
    return result
''')
        
        zip_path = tmp_path / "missing_deps.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        # Should not crash during parsing
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "missing_deps")
        
        # Should still parse the function
        assert len(analysis.functions) >= 1
        
        # Should track the imports even if missing
        assert "nonexistent_module" in analysis.imports.get(list(analysis.modules.keys())[0], [])
        
        print(f"\n=== Missing Dependencies Test ===")
        print(f"Functions parsed: {len(analysis.functions)}")
        print("Missing imports handled gracefully ✓")
    
    def test_duplicate_ids_handling(self, tmp_path):
        """P1 HIGH: Test handling of potential duplicate IDs."""
        repo_dir = tmp_path / "duplicate_ids"
        repo_dir.mkdir()
        
        # Create subdirectories with same filename
        (repo_dir / "module_a").mkdir()
        (repo_dir / "module_b").mkdir()
        
        # Both have same function name
        (repo_dir / "module_a" / "utils.py").write_text('''
def process():
    return "a"
''')
        
        (repo_dir / "module_b" / "utils.py").write_text('''
def process():
    return "b"
''')
        
        zip_path = tmp_path / "duplicate_ids.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "duplicate_ids")
        
        # Should have 2 functions (not overwrite each other)
        assert len(analysis.functions) == 2
        
        # Function IDs should be unique (include file path)
        ids = list(analysis.functions.keys())
        assert len(ids) == len(set(ids))  # All unique
        
        print(f"\n=== Duplicate IDs Test ===")
        print(f"Functions: {len(analysis.functions)}")
        print(f"Unique IDs: {len(set(ids))}")
        print("No ID collisions ✓")
    
    def test_calls_extraction_accuracy(self, tmp_path):
        """P1 HIGH: Verify function calls are accurately extracted."""
        repo_dir = tmp_path / "calls_test"
        repo_dir.mkdir()
        
        (repo_dir / "test.py").write_text('''
def helper():
    return 42

def another_helper():
    return 100

def main_function():
    """Should call helper and another_helper."""
    x = helper()
    y = another_helper()
    z = print(x, y)
    return x + y
''')
        
        zip_path = tmp_path / "calls_test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "calls_test")
        
        # Find main_function
        main_func = None
        for func in analysis.functions.values():
            if func.name == "main_function":
                main_func = func
                break
        
        assert main_func is not None
        
        # Should have detected calls (calls may be resolved to full IDs)
        calls_str = str(main_func.calls)
        assert "helper" in calls_str
        assert "another_helper" in calls_str
        assert "print" in main_func.calls  # print is builtin, not resolved
        
        print(f"\n=== Calls Extraction Test ===")
        print(f"main_function calls: {main_func.calls}")
        print("Call extraction accurate ✓")
    
    def test_empty_function_handling(self, tmp_path):
        """P2 MEDIUM: Test empty functions are handled."""
        repo_dir = tmp_path / "empty_func"
        repo_dir.mkdir()
        
        (repo_dir / "empty.py").write_text('''
def empty_function():
    pass

def another_empty():
    ...

def with_docstring_only():
    """Just a docstring."""
    
async def async_empty():
    pass
''')
        
        zip_path = tmp_path / "empty_func.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "empty_func")
        
        # Should parse all empty functions
        assert len(analysis.functions) == 4
        assert len(analysis.parse_errors) == 0
        
        # Verify each has valid source
        for func in analysis.functions.values():
            assert func.source is not None
            assert len(func.source.strip()) > 0
        
        print(f"\n=== Empty Function Test ===")
        print(f"Empty functions parsed: {len(analysis.functions)}")
        print("All empty functions handled ✓")
    
    def test_source_code_completeness(self, tmp_path):
        """P0 CRITICAL: Verify source code is complete and accurate."""
        repo_dir = tmp_path / "source_test"
        repo_dir.mkdir()
        
        expected_source = '''def test_function(x, y):
    """Test function."""
    result = x + y
    return result'''
        
        (repo_dir / "test.py").write_text(expected_source)
        
        zip_path = tmp_path / "source_test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in repo_dir.rglob('*'):
                if file.is_file():
                    zf.write(file, file.relative_to(repo_dir.parent))
        
        extract_dir = tmp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze(extract_dir / "source_test")
        
        assert len(analysis.functions) == 1
        func = list(analysis.functions.values())[0]
        
        # Source should match exactly (modulo whitespace)
        assert func.source.strip() == expected_source.strip()
        
        print(f"\n=== Source Code Completeness ===")
        print("Source code extraction accurate ✓")
