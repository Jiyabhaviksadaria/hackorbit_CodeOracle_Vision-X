"""Internal repository analysis models - richer than external contracts."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum


class Language(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"


class SymbolType(str, Enum):
    """Type of code symbol."""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    METHOD = "method"


class ParseStatus(str, Enum):
    """Parse result status."""
    SUPPORTED = "supported"
    INFERRED = "inferred"
    UNCERTAIN = "uncertain"
    PARSE_ERROR = "parse_error"
    UNSUPPORTED = "unsupported"


@dataclass
class FileInfo:
    """Information about a file in the repository."""
    path: str
    relative_path: str
    language: Optional[Language]
    size: int
    loc: int = 0
    supported: bool = True
    parse_status: ParseStatus = ParseStatus.SUPPORTED
    parse_error: Optional[str] = None


@dataclass
class FunctionInfo:
    """Internal rich function information."""
    id: str
    name: str
    file: str
    start_line: int
    end_line: int
    source: str
    parameters: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    complexity: Optional[int] = None
    status: ParseStatus = ParseStatus.SUPPORTED


@dataclass
class ClassInfo:
    """Internal class information."""
    id: str
    name: str
    file: str
    start_line: int
    end_line: int
    source: str
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    status: ParseStatus = ParseStatus.SUPPORTED


@dataclass
class ModuleInfo:
    """Internal module information."""
    id: str
    name: str
    file: str
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    loc: int = 0


@dataclass
class RepositoryAnalysis:
    """
    Internal repository analysis model.
    This is RICHER than external contracts.
    Use ParsedChunkAdapter to convert to external ParsedChunk format.
    """
    repository_id: str
    name: str
    root_path: str
    
    # Metrics
    total_loc: int = 0
    languages: Set[Language] = field(default_factory=set)
    
    # Files
    files: List[FileInfo] = field(default_factory=list)
    supported_files: List[FileInfo] = field(default_factory=list)
    unsupported_files: List[FileInfo] = field(default_factory=list)
    
    # Symbols
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    
    # Dependencies
    imports: Dict[str, List[str]] = field(default_factory=dict)
    calls: Dict[str, List[str]] = field(default_factory=dict)
    
    # Errors
    parse_errors: List[Dict[str, str]] = field(default_factory=list)
    
    def add_file(self, file_info: FileInfo):
        """Add file to analysis."""
        self.files.append(file_info)
        if file_info.supported:
            self.supported_files.append(file_info)
        else:
            self.unsupported_files.append(file_info)
        
        if file_info.language:
            self.languages.add(file_info.language)
        
        self.total_loc += file_info.loc
    
    def add_function(self, func: FunctionInfo):
        """Add function to analysis."""
        self.functions[func.id] = func
    
    def add_class(self, cls: ClassInfo):
        """Add class to analysis."""
        self.classes[cls.id] = cls
    
    def add_module(self, module: ModuleInfo):
        """Add module to analysis."""
        self.modules[module.id] = module
    
    def add_parse_error(self, file: str, error: str):
        """Record parse error."""
        self.parse_errors.append({"file": file, "error": error})
