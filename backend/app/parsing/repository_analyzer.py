"""Main repository analyzer that orchestrates parsing."""
from pathlib import Path
from typing import Optional
import uuid

from ..models.repository import RepositoryAnalysis, Language, ParseStatus
from ..ingestion.file_tree import build_file_tree
from .python_parser import PythonParser
from .javascript_parser import JavaScriptParser, TREE_SITTER_AVAILABLE
from .call_resolver import CallResolver


class RepositoryAnalyzer:
    """
    Main analyzer that coordinates parsing across languages.
    Converts repository → RepositoryAnalysis.
    """

    def __init__(self):
        self.python_parser = PythonParser()
        self.js_parser: Optional[JavaScriptParser] = None
        self.call_resolver = CallResolver()

        if TREE_SITTER_AVAILABLE:
            try:
                self.js_parser = JavaScriptParser()
            except Exception as e:
                print(f"Warning: JavaScript parser init failed: {e}")

    def analyze(
        self,
        root_path: Path,
        repository_name: Optional[str] = None
    ) -> RepositoryAnalysis:
        """
        Analyze a repository directory.

        Returns:
            RepositoryAnalysis with all extracted information.
        """
        if not repository_name:
            repository_name = root_path.name

        analysis = RepositoryAnalysis(
            repository_id=str(uuid.uuid4()),
            name=repository_name,
            root_path=str(root_path)
        )

        # Build file tree with metadata
        for file_info in build_file_tree(root_path):
            analysis.add_file(file_info)

        # Parse every supported file - errors are isolated, never fatal
        for file_info in analysis.supported_files:
            self._parse_file(Path(file_info.path), file_info.language, analysis)

        # Basic cross-file call resolution
        self.call_resolver.resolve(analysis)

        return analysis

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_file(
        self,
        path: Path,
        language: Optional[Language],
        analysis: RepositoryAnalysis
    ) -> None:
        if not language:
            return

        try:
            if language == Language.PYTHON:
                module, functions, classes, error = self.python_parser.parse_file(path)

            elif language == Language.JAVASCRIPT:
                if not self.js_parser:
                    analysis.add_parse_error(str(path), "JavaScript parser not available")
                    return
                module, functions, classes, error = self.js_parser.parse_file(path)

            else:
                return

            if error:
                analysis.add_parse_error(str(path), error)
                for f in analysis.files:
                    if f.path == str(path):
                        f.parse_status = ParseStatus.PARSE_ERROR
                        f.parse_error = error
                return

            if module:
                analysis.add_module(module)
                analysis.imports[module.id] = module.imports

            for func in functions:
                analysis.add_function(func)
                if func.calls:
                    analysis.calls[func.id] = func.calls

            for cls in classes:
                analysis.add_class(cls)

        except Exception as e:
            analysis.add_parse_error(str(path), f"Unexpected error: {e}")
