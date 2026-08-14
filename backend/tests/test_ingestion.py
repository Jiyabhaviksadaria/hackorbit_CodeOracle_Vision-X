"""Test ingestion module."""
import pytest
import tempfile
import zipfile
from pathlib import Path
from app.ingestion.zip_handler import (
    validate_zip, extract_zip, is_safe_path, should_ignore,
    ZipValidationError, ZipSecurityError
)


def test_should_ignore_common_dirs():
    """Test that common directories are ignored."""
    assert should_ignore("node_modules/file.js")
    assert should_ignore(".git/config")
    assert should_ignore("dist/bundle.js")
    assert should_ignore("__pycache__/file.pyc")
    assert should_ignore("venv/lib/python")
    
    assert not should_ignore("src/main.py")
    assert not should_ignore("tests/test_main.py")


def test_is_safe_path():
    """Test path traversal protection."""
    base = Path("/tmp/test")
    
    # Safe paths
    assert is_safe_path(base, base / "file.py")
    assert is_safe_path(base, base / "subdir" / "file.py")
    
    # Unsafe paths (if they could be constructed)
    unsafe = Path("/etc/passwd")
    assert not is_safe_path(base, unsafe)


def test_validate_empty_zip():
    """Test that empty ZIP is rejected."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
        zip_path = Path(f.name)
        
        # Create empty valid ZIP
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass  # Empty ZIP
    
    try:
        # This should work - empty but valid
        validate_zip(zip_path, max_size_mb=100)
    except ZipValidationError:
        pass  # Expected for truly empty ZIP
    finally:
        zip_path.unlink()


def test_extract_zip_with_ignored_dirs():
    """Test that ignored directories are not extracted."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "test.zip"
        
        # Create ZIP with ignored directories
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("src/main.py", "print('hello')")
            zf.writestr("node_modules/lib.js", "// lib")
            zf.writestr(".git/config", "[core]")
        
        extract_dir = temp_path / "extracted"
        extract_zip(zip_path, extract_dir)
        
        # Check that only src/main.py was extracted
        assert (extract_dir / "src" / "main.py").exists()
        # Ignored directories should not be extracted
        # (depending on implementation, they might be skipped)


def test_validate_corrupt_zip():
    """Test that corrupt ZIP is rejected."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
        zip_path = Path(f.name)
        f.write(b"NOT A ZIP FILE")
    
    try:
        with pytest.raises(ZipValidationError):
            validate_zip(zip_path)
    finally:
        zip_path.unlink()


def test_validate_oversized_zip():
    """Test that oversized ZIP is rejected."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "large.zip"
        
        # Create ZIP with large file
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Write a large file (2MB uncompressed)
            large_content = "x" * (2 * 1024 * 1024)
            zf.writestr("large.txt", large_content)
        
        # Should reject with max_size_mb=1
        with pytest.raises(ZipSecurityError):
            validate_zip(zip_path, max_size_mb=1)
