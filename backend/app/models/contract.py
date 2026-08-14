"""
Contract models - LOCKED external interfaces.
These match CONTRACT.md exactly and MUST NOT be changed without team sync.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ParsedChunk(BaseModel):
    """
    LOCKED CONTRACT - matches CONTRACT.md §3.
    DO NOT modify without team approval.
    """
    file: str
    language: Literal["python", "javascript"]
    type: Literal["function", "class", "module"]
    name: str
    start_line: int
    end_line: int
    source: str
    calls: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)


class JobStatus(BaseModel):
    """Job status response - LOCKED."""
    status: Literal["queued", "parsing", "explaining", "testing", "refactoring", "done", "error"]
    progress: int = Field(ge=0, le=100)
    error: Optional[str] = None


class Explanation(BaseModel):
    """Explanation schema - LOCKED."""
    modules: List[dict] = Field(default_factory=list)
    functions: List[dict] = Field(default_factory=list)


class DepGraph(BaseModel):
    """Dependency graph schema - LOCKED."""
    nodes: List[dict] = Field(default_factory=list)
    edges: List[dict] = Field(default_factory=list)


class TestResult(BaseModel):
    """Test result schema - LOCKED."""
    test_files: List[dict] = Field(default_factory=list)
    coverage_percent: float = 0.0
    passed: int = 0
    failed: int = 0
    log: str = ""


class RefactorResult(BaseModel):
    """Refactor result schema - LOCKED."""
    files: List[dict] = Field(default_factory=list)
