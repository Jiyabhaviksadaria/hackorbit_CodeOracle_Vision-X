"""Python AST parser using stdlib ast module."""
import ast
from pathlib import Path
from typing import List, Optional, Set
from ..models.repository import (
    FunctionInfo, ClassInfo, ModuleInfo, 
    ParseStatus, SymbolType
)


class PythonParser:
    """Parse Python files using AST."""
    
    def parse_file(self, file_path: Path) -> tuple[
        Optional[ModuleInfo],
        List[FunctionInfo],
        List[ClassInfo],
        Optional[str]
    ]:
        """
        Parse a Python file.
        
        Returns:
            (module_info, functions, classes, error)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(file_path))
            
            module_id = str(file_path)
            module_name = file_path.stem
            
            # Extract module-level info
            imports = self._extract_imports(tree)
            
            # Extract functions and classes
            functions = []
            classes = []

            # Collect all method nodes inside classes so we don't double-extract them
            method_nodes: set = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_nodes.add(id(item))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Only extract as top-level function if NOT a method
                    if id(node) not in method_nodes:
                        func_info = self._extract_function(node, file_path, source)
                        if func_info:
                            functions.append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = self._extract_class(node, file_path, source)
                    if class_info:
                        classes.append(class_info)

                        # Extract methods with class-qualified ID
                        for item in node.body:
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                method_info = self._extract_method(
                                    item, node.name, file_path, source
                                )
                                if method_info:
                                    functions.append(method_info)
            
            # Create module info
            module = ModuleInfo(
                id=module_id,
                name=module_name,
                file=str(file_path),
                imports=imports,
                functions=[f.id for f in functions],
                classes=[c.id for c in classes],
                loc=len(source.splitlines())
            )
            
            return module, functions, classes, None
            
        except SyntaxError as e:
            return None, [], [], f"Syntax error: {e}"
        except Exception as e:
            return None, [], [], f"Parse error: {e}"
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                for alias in node.names:
                    imports.append(alias.name)
        
        return imports
    
    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: Path,
        source: str
    ) -> Optional[FunctionInfo]:
        """Extract function information."""
        try:
            func_id = f"{file_path}::{node.name}"
            
            # Get source lines
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            
            # Extract source
            source_lines = source.splitlines()
            func_source = '\n'.join(
                source_lines[start_line - 1:end_line]
            )
            
            # Extract parameters
            params = [arg.arg for arg in node.args.args]
            
            # Extract decorators
            decorators = [
                ast.unparse(dec) if hasattr(ast, 'unparse') else ''
                for dec in node.decorator_list
            ]
            
            # Extract calls
            calls = self._extract_calls(node)
            
            # Extract return annotation
            returns = None
            if node.returns:
                try:
                    returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
                except:
                    pass
            
            return FunctionInfo(
                id=func_id,
                name=node.name,
                file=str(file_path),
                start_line=start_line,
                end_line=end_line,
                source=func_source,
                parameters=params,
                returns=returns,
                calls=calls,
                decorators=decorators,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                status=ParseStatus.SUPPORTED
            )
            
        except Exception:
            return None
    
    def _extract_method(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str,
        file_path: Path,
        source: str
    ) -> Optional[FunctionInfo]:
        """Extract method information."""
        func_info = self._extract_function(node, file_path, source)
        if func_info:
            # Update ID to include class
            func_info.id = f"{file_path}::{class_name}.{node.name}"
        return func_info
    
    def _extract_class(
        self,
        node: ast.ClassDef,
        file_path: Path,
        source: str
    ) -> Optional[ClassInfo]:
        """Extract class information."""
        try:
            class_id = f"{file_path}::{node.name}"
            
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            
            source_lines = source.splitlines()
            class_source = '\n'.join(
                source_lines[start_line - 1:end_line]
            )
            
            # Extract methods
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            
            # Extract base classes
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
            
            # Extract decorators
            decorators = [
                ast.unparse(dec) if hasattr(ast, 'unparse') else ''
                for dec in node.decorator_list
            ]
            
            return ClassInfo(
                id=class_id,
                name=node.name,
                file=str(file_path),
                start_line=start_line,
                end_line=end_line,
                source=class_source,
                methods=methods,
                bases=bases,
                decorators=decorators,
                status=ParseStatus.SUPPORTED
            )
            
        except Exception:
            return None
    
    def _extract_calls(self, node: ast.AST) -> List[str]:
        """Extract function calls from a node."""
        calls = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    # For method calls like obj.method()
                    if isinstance(child.func.value, ast.Name):
                        calls.append(f"{child.func.value.id}.{child.func.attr}")
                    else:
                        calls.append(child.func.attr)
        
        return calls
