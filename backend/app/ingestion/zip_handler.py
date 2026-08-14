"""Safe ZIP extraction and validation."""
import os
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import tempfile
import shutil


class ZipValidationError(Exception):
    """ZIP validation failed."""
    pass


class ZipSecurityError(Exception):
    """ZIP contains security issue."""
    pass


# Directories to ignore during extraction
IGNORED_DIRS = {
    '.git',
    'node_modules',
    'dist',
    'build',
    '__pycache__',
    '.venv',
    'venv',
    'virtualenv',
    'env',
    '.pytest_cache',
    'coverage',
    '.tox',
    '.eggs',
    'target',
    'bin',
    'obj',
}


def is_safe_path(base_path: Path, target_path: Path) -> bool:
    """
    Check if target_path is safely within base_path.
    Prevents path traversal attacks.
    """
    try:
        resolved_target = target_path.resolve()
        resolved_base = base_path.resolve()
        return str(resolved_target).startswith(str(resolved_base))
    except (ValueError, OSError):
        return False


def should_ignore(path: str) -> bool:
    """Check if path should be ignored."""
    parts = Path(path).parts
    for part in parts:
        if part in IGNORED_DIRS or part.startswith('.'):
            return True
    return False


def validate_zip(zip_path: Path, max_size_mb: int = 100) -> None:
    """
    Validate ZIP file before extraction.
    
    Args:
        zip_path: Path to ZIP file
        max_size_mb: Maximum allowed uncompressed size in MB
        
    Raises:
        ZipValidationError: If ZIP is invalid
        ZipSecurityError: If ZIP has security issues
    """
    if not zip_path.exists():
        raise ZipValidationError("ZIP file does not exist")
    
    if not zipfile.is_zipfile(zip_path):
        raise ZipValidationError("File is not a valid ZIP archive")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check for corruption
            bad_file = zf.testzip()
            if bad_file is not None:
                raise ZipValidationError(f"Corrupt file in ZIP: {bad_file}")
            
            # Check uncompressed size
            total_size = sum(info.file_size for info in zf.infolist())
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if total_size > max_size_bytes:
                raise ZipSecurityError(
                    f"ZIP too large: {total_size / (1024*1024):.1f}MB > {max_size_mb}MB"
                )
            
            # Check file count
            file_count = len(zf.infolist())
            if file_count > 10000:
                raise ZipSecurityError(f"Too many files: {file_count} > 10000")
            
    except zipfile.BadZipFile as e:
        raise ZipValidationError(f"Bad ZIP file: {e}")


def extract_zip(
    zip_path: Path,
    extract_to: Path,
    max_size_mb: int = 100
) -> Path:
    """
    Safely extract ZIP file to workspace.
    
    Args:
        zip_path: Path to ZIP file
        extract_to: Directory to extract to
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        Path to extracted directory
        
    Raises:
        ZipValidationError: If ZIP is invalid
        ZipSecurityError: If ZIP has security issues
    """
    # Validate first
    validate_zip(zip_path, max_size_mb)
    
    # Create extraction directory
    extract_to.mkdir(parents=True, exist_ok=True)
    
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                # Skip directories
                if info.is_dir():
                    continue
                
                # Check for path traversal
                member_path = extract_to / info.filename
                if not is_safe_path(extract_to, member_path):
                    raise ZipSecurityError(
                        f"Path traversal detected: {info.filename}"
                    )
                
                # Skip ignored directories
                if should_ignore(info.filename):
                    continue
                
                # Extract file
                try:
                    zf.extract(info, extract_to)
                    extracted_files.append(member_path)
                except Exception as e:
                    # Log but continue
                    print(f"Warning: Could not extract {info.filename}: {e}")
        
        if not extracted_files:
            raise ZipValidationError("ZIP contains no valid files")
        
        return extract_to
        
    except Exception as e:
        # Cleanup on failure
        if extract_to.exists():
            shutil.rmtree(extract_to, ignore_errors=True)
        raise


def create_workspace(job_id: str, workspace_root: Path) -> Tuple[Path, Path, Path, Path]:
    """
    Create workspace structure for a job.
    
    Returns:
        (workspace_dir, original_dir, working_dir, generated_tests_dir)
    """
    workspace_dir = workspace_root / f"job_{job_id}"
    original_dir = workspace_dir / "original"
    working_dir = workspace_dir / "working"
    generated_tests_dir = workspace_dir / "generated_tests"
    
    workspace_dir.mkdir(parents=True, exist_ok=True)
    original_dir.mkdir(exist_ok=True)
    working_dir.mkdir(exist_ok=True)
    generated_tests_dir.mkdir(exist_ok=True)
    
    return workspace_dir, original_dir, working_dir, generated_tests_dir


def cleanup_workspace(workspace_dir: Path) -> None:
    """Clean up workspace directory."""
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir, ignore_errors=True)
