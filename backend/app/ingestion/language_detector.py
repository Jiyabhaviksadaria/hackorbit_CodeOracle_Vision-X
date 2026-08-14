"""Deterministic language detection."""
from pathlib import Path
from typing import Optional, Dict, List
from ..models.repository import Language


# File extension to language mapping
LANGUAGE_EXTENSIONS = {
    '.py': Language.PYTHON,
    '.js': Language.JAVASCRIPT,
    '.jsx': Language.JAVASCRIPT,
}


def detect_language(file_path: Path) -> Optional[Language]:
    """
    Detect programming language from file extension.
    Deterministic - never ask AI.
    
    Args:
        file_path: Path to file
        
    Returns:
        Language or None if unsupported
    """
    suffix = file_path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(suffix)


def scan_repository_languages(root_path: Path) -> Dict[Language, int]:
    """
    Scan repository and count files by language.
    
    Args:
        root_path: Root directory of repository
        
    Returns:
        Dictionary mapping Language to file count
    """
    language_counts: Dict[Language, int] = {}
    
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        lang = detect_language(file_path)
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1
    
    return language_counts


def get_supported_files(root_path: Path) -> List[Path]:
    """
    Get all supported source files in repository.
    
    Args:
        root_path: Root directory
        
    Returns:
        List of supported file paths
    """
    supported_files = []
    
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        if detect_language(file_path):
            supported_files.append(file_path)
    
    return supported_files


def is_supported_language(file_path: Path) -> bool:
    """Check if file is a supported language."""
    return detect_language(file_path) is not None
