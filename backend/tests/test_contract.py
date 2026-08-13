"""
Contract tests - verify ParsedChunk matches CONTRACT.md exactly.
CRITICAL: These tests protect other team members.
"""
import pytest
from app.models.contract import ParsedChunk
from app.models.repository import FunctionInfo, ClassInfo, Language
from app.parsing.contract_adapter import ParsedChunkAdapter


def test_parsed_chunk_required_fields():
    """Verify ParsedChunk has all required CONTRACT.md fields."""
    chunk = ParsedChunk(
        file="test.py",
        language="python",
        type="function",
        name="test_func",
        start_line=1,
        end_line=10,
        source="def test_func(): pass",
        calls=[],
        imports=[]
    )
    
    # All required fields must exist
    assert hasattr(chunk, 'file')
    assert hasattr(chunk, 'language')
    assert hasattr(chunk, 'type')
    assert hasattr(chunk, 'name')
    assert hasattr(chunk, 'start_line')
    assert hasattr(chunk, 'end_line')
    assert hasattr(chunk, 'source')
    assert hasattr(chunk, 'calls')
    assert hasattr(chunk, 'imports')


def test_parsed_chunk_field_types():
    """Verify ParsedChunk field types match CONTRACT.md."""
    chunk = ParsedChunk(
        file="test.py",
        language="python",
        type="function",
        name="test_func",
        start_line=1,
        end_line=10,
        source="def test_func(): pass",
        calls=["other_func"],
        imports=["os", "sys"]
    )
    
    assert isinstance(chunk.file, str)
    assert isinstance(chunk.language, str)
    assert chunk.language in ["python", "javascript"]
    assert isinstance(chunk.type, str)
    assert chunk.type in ["function", "class", "module"]
    assert isinstance(chunk.name, str)
    assert isinstance(chunk.start_line, int)
    assert isinstance(chunk.end_line, int)
    assert isinstance(chunk.source, str)
    assert isinstance(chunk.calls, list)
    assert isinstance(chunk.imports, list)


def test_adapter_preserves_contract():
    """Verify adapter converts to valid ParsedChunk."""
    func = FunctionInfo(
        id="test.py::test_func",
        name="test_func",
        file="test.py",
        start_line=1,
        end_line=10,
        source="def test_func(): pass",
        parameters=["x", "y"],
        calls=["helper"],
        imports=["os"]
    )
    
    chunk = ParsedChunkAdapter.from_function(func, Language.PYTHON)
    
    # Verify it's a valid ParsedChunk
    assert isinstance(chunk, ParsedChunk)
    assert chunk.file == "test.py"
    assert chunk.language == "python"
    assert chunk.type == "function"
    assert chunk.name == "test_func"
    assert chunk.start_line == 1
    assert chunk.end_line == 10
    assert chunk.source == "def test_func(): pass"
    assert "helper" in chunk.calls
    assert "os" in chunk.imports


def test_parsed_chunk_json_serializable():
    """Verify ParsedChunk can be serialized to JSON."""
    chunk = ParsedChunk(
        file="test.py",
        language="python",
        type="function",
        name="test_func",
        start_line=1,
        end_line=10,
        source="def test_func(): pass",
        calls=[],
        imports=[]
    )
    
    # Pydantic models have .model_dump() for JSON serialization
    json_data = chunk.model_dump()
    
    assert isinstance(json_data, dict)
    assert json_data['file'] == "test.py"
    assert json_data['language'] == "python"
    assert json_data['type'] == "function"


def test_calls_and_imports_are_lists():
    """Verify calls and imports are always lists, never None."""
    chunk = ParsedChunk(
        file="test.py",
        language="python",
        type="function",
        name="test_func",
        start_line=1,
        end_line=10,
        source="def test_func(): pass"
    )
    
    # Default should be empty list, not None
    assert isinstance(chunk.calls, list)
    assert isinstance(chunk.imports, list)
    assert len(chunk.calls) == 0
    assert len(chunk.imports) == 0
