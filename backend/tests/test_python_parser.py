"""Test Python parser."""
import pytest
import tempfile
from pathlib import Path
from app.parsing.python_parser import PythonParser


def test_parse_simple_function():
    """Test parsing a simple function."""
    parser = PythonParser()
    
    source = '''
def hello(name):
    print(f"Hello, {name}")
    return name
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        file_path = Path(f.name)
    
    try:
        module, functions, classes, error = parser.parse_file(file_path)
        
        assert error is None
        assert len(functions) == 1
        assert len(classes) == 0
        
        func = functions[0]
        assert func.name == "hello"
        assert "name" in func.parameters
        assert func.start_line > 0
        assert func.end_line > func.start_line
        assert "def hello" in func.source
    
    finally:
        file_path.unlink()


def test_parse_class_with_methods():
    """Test parsing a class with methods."""
    parser = PythonParser()
    
    source = '''
class Calculator:
    def add(self, x, y):
        return x + y
    
    def subtract(self, x, y):
        return x - y
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        file_path = Path(f.name)
    
    try:
        module, functions, classes, error = parser.parse_file(file_path)
        
        assert error is None
        assert len(classes) == 1
        
        cls = classes[0]
        assert cls.name == "Calculator"
        assert "add" in cls.methods
        assert "subtract" in cls.methods
        
        # Methods should also be in functions list
        assert len(functions) == 2
        method_names = [f.name for f in functions]
        assert "add" in method_names
        assert "subtract" in method_names
    
    finally:
        file_path.unlink()


def test_parse_with_imports():
    """Test that imports are extracted."""
    parser = PythonParser()
    
    source = '''
import os
import sys
from pathlib import Path
from typing import List, Dict

def process():
    pass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        file_path = Path(f.name)
    
    try:
        module, functions, classes, error = parser.parse_file(file_path)
        
        assert error is None
        assert module is not None
        
        # Check imports
        assert "os" in module.imports
        assert "sys" in module.imports
        assert "pathlib" in module.imports or "Path" in module.imports
    
    finally:
        file_path.unlink()


def test_parse_with_function_calls():
    """Test that function calls are extracted."""
    parser = PythonParser()
    
    source = '''
def helper():
    return 42

def main():
    result = helper()
    print(result)
    return result
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        file_path = Path(f.name)
    
    try:
        module, functions, classes, error = parser.parse_file(file_path)
        
        assert error is None
        assert len(functions) == 2
        
        # Find main function
        main_func = next(f for f in functions if f.name == "main")
        
        # Check that it calls helper and print
        assert "helper" in main_func.calls
        assert "print" in main_func.calls
    
    finally:
        file_path.unlink()


def test_parse_malformed_python():
    """Test that malformed Python returns error."""
    parser = PythonParser()
    
    source = '''
def broken(
    # Missing closing parenthesis and colon
    pass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        file_path = Path(f.name)
    
    try:
        module, functions, classes, error = parser.parse_file(file_path)
        
        # Should return error, not crash
        assert error is not None
        assert "error" in error.lower() or "syntax" in error.lower()
    
    finally:
        file_path.unlink()


def test_parse_async_function():
    """Test parsing async functions."""
    parser = PythonParser()
    
    source = '''
async def fetch_data():
    return await some_async_call()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        file_path = Path(f.name)
    
    try:
        module, functions, classes, error = parser.parse_file(file_path)
        
        assert error is None
        assert len(functions) == 1
        
        func = functions[0]
        assert func.name == "fetch_data"
        assert func.is_async is True
    
    finally:
        file_path.unlink()


def test_parse_decorators():
    """Test that decorators are extracted."""
    parser = PythonParser()
    
    source = '''
@property
@staticmethod
def my_func():
    pass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        file_path = Path(f.name)
    
    try:
        module, functions, classes, error = parser.parse_file(file_path)
        
        assert error is None
        assert len(functions) == 1
        
        func = functions[0]
        # Decorators should be captured
        assert len(func.decorators) > 0
    
    finally:
        file_path.unlink()
