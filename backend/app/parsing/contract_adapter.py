"""
Adapter to convert internal models to LOCKED ParsedChunk contract.
DO NOT change ParsedChunk - it's locked by CONTRACT.md.
"""
from typing import List
from ..models.repository import FunctionInfo, ClassInfo, ModuleInfo, Language
from ..models.contract import ParsedChunk


class ParsedChunkAdapter:
    """
    Converts internal rich models to external ParsedChunk contract.
    This protects other teams from internal model changes.
    """
    
    @staticmethod
    def from_function(func: FunctionInfo, language: Language) -> ParsedChunk:
        """Convert FunctionInfo to ParsedChunk."""
        return ParsedChunk(
            file=func.file,
            language=language.value,
            type="function",
            name=func.name,
            start_line=func.start_line,
            end_line=func.end_line,
            source=func.source,
            calls=func.calls,
            imports=func.imports
        )
    
    @staticmethod
    def from_class(cls: ClassInfo, language: Language) -> ParsedChunk:
        """Convert ClassInfo to ParsedChunk."""
        return ParsedChunk(
            file=cls.file,
            language=language.value,
            type="class",
            name=cls.name,
            start_line=cls.start_line,
            end_line=cls.end_line,
            source=cls.source,
            calls=[],  # Classes don't have direct calls
            imports=[]
        )
    
    @staticmethod
    def from_module(module: ModuleInfo, language: Language, source: str) -> ParsedChunk:
        """Convert ModuleInfo to ParsedChunk."""
        return ParsedChunk(
            file=module.file,
            language=language.value,
            type="module",
            name=module.name,
            start_line=1,
            end_line=module.loc,
            source=source,
            calls=[],
            imports=module.imports
        )
    
    @staticmethod
    def from_repository_analysis(
        functions: List[FunctionInfo],
        classes: List[ClassInfo],
        language: Language
    ) -> List[ParsedChunk]:
        """
        Convert repository analysis to list of ParsedChunks.
        This is what gets sent to AI/ML team.
        """
        chunks = []
        
        for func in functions:
            chunks.append(
                ParsedChunkAdapter.from_function(func, language)
            )
        
        for cls in classes:
            chunks.append(
                ParsedChunkAdapter.from_class(cls, language)
            )
        
        return chunks
