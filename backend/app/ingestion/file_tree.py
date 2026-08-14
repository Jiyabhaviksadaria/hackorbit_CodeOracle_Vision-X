"""File tree generation."""
from pathlib import Path
from typing import List, Dict
from .language_detector import detect_language, is_supported_language
from ..models.repository import FileInfo, Language


def calculate_loc(file_path: Path) -> int:
    """
    Calculate lines of code for a file.
    Simple deterministic rule: count non-empty, non-comment lines.
    
    Args:
        file_path: Path to source file
        
    Returns:
        Line count
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        loc = 0
        for line in lines:
            stripped = line.strip()
            # Count non-empty lines that don't start with comment
            if stripped and not stripped.startswith('#') and not stripped.startswith('//'):
                loc += 1
        
        return loc
        
    except Exception:
        return 0


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    try:
        return file_path.stat().st_size
    except Exception:
        return 0


def build_file_tree(root_path: Path) -> List[FileInfo]:
    """
    Build file tree with metadata.
    
    Args:
        root_path: Root directory of repository
        
    Returns:
        List of FileInfo objects
    """
    files = []
    
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Get relative path
        try:
            relative_path = file_path.relative_to(root_path)
        except ValueError:
            continue
        
        # Detect language
        language = detect_language(file_path)
        supported = language is not None
        
        # Calculate LOC for supported files
        loc = 0
        if supported:
            loc = calculate_loc(file_path)
        
        file_info = FileInfo(
            path=str(file_path),
            relative_path=str(relative_path),
            language=language,
            size=get_file_size(file_path),
            loc=loc,
            supported=supported
        )
        
        files.append(file_info)
    
    return files


def calculate_total_loc(files: List[FileInfo]) -> int:
    """Calculate total LOC across all supported files."""
    return sum(f.loc for f in files if f.supported)


def group_files_by_language(files: List[FileInfo]) -> Dict[Language, List[FileInfo]]:
    """Group files by language."""
    grouped: Dict[Language, List[FileInfo]] = {}
    
    for file_info in files:
        if file_info.language:
            if file_info.language not in grouped:
                grouped[file_info.language] = []
            grouped[file_info.language].append(file_info)
    
    return grouped
