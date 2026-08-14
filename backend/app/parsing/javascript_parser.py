"""JavaScript parser using tree-sitter."""
from pathlib import Path
from typing import List, Optional
try:
    import tree_sitter_javascript as tsjs
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from ..models.repository import (
    FunctionInfo, ClassInfo, ModuleInfo,
    ParseStatus
)


class JavaScriptParser:
    """Parse JavaScript files using tree-sitter."""
    
    def __init__(self):
        """Initialize parser."""
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter-javascript not available. "
                "Install: pip install tree-sitter tree-sitter-javascript"
            )
        
        self.language = Language(tsjs.language(), "javascript")
        self.parser = Parser()
        self.parser.set_language(self.language)
    
    def parse_file(self, file_path: Path) -> tuple[
        Optional[ModuleInfo],
        List[FunctionInfo],
        List[ClassInfo],
        Optional[str]
    ]:
        """
        Parse a JavaScript file.
        
        Returns:
            (module_info, functions, classes, error)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            source_bytes = source.encode('utf-8')
            tree = self.parser.parse(source_bytes)
            
            functions = []
            classes = []
            imports = []
            
            # Walk the tree
            self._walk_node(tree.root_node, functions, classes, imports, file_path, source)
            
            # Create module info
            module = ModuleInfo(
                id=str(file_path),
                name=file_path.stem,
                file=str(file_path),
                imports=imports,
                functions=[f.id for f in functions],
                classes=[c.id for c in classes],
                loc=len(source.splitlines())
            )
            
            return module, functions, classes, None
            
        except Exception as e:
            return None, [], [], f"Parse error: {e}"
    
    def _walk_node(
        self,
        node: 'Node',
        functions: List[FunctionInfo],
        classes: List[ClassInfo],
        imports: List[str],
        file_path: Path,
        source: str
    ):
        """Recursively walk tree nodes."""
        node_type = node.type
        
        # Extract functions
        if node_type in ('function_declaration', 'function', 'arrow_function', 'method_definition'):
            func_info = self._extract_function(node, file_path, source)
            if func_info:
                functions.append(func_info)
        
        # Extract classes
        elif node_type == 'class_declaration':
            class_info = self._extract_class(node, file_path, source)
            if class_info:
                classes.append(class_info)
        
        # Extract imports
        elif node_type in ('import_statement', 'import_declaration'):
            import_info = self._extract_import(node, source)
            if import_info:
                imports.extend(import_info)
        
        # Recurse to children
        for child in node.children:
            self._walk_node(child, functions, classes, imports, file_path, source)
    
    def _extract_function(
        self,
        node: 'Node',
        file_path: Path,
        source: str
    ) -> Optional[FunctionInfo]:
        """Extract function information."""
        try:
            # Get function name
            name = None
            for child in node.children:
                if child.type == 'identifier':
                    name = self._get_node_text(child, source)
                    break
                elif child.type == 'property_identifier':
                    name = self._get_node_text(child, source)
                    break
            
            if not name:
                name = '<anonymous>'
            
            func_id = f"{file_path}::{name}"
            
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Get source
            func_source = self._get_node_text(node, source)
            
            # Extract parameters
            params = self._extract_parameters(node, source)
            
            # Extract calls
            calls = self._extract_calls(node, source)
            
            return FunctionInfo(
                id=func_id,
                name=name,
                file=str(file_path),
                start_line=start_line,
                end_line=end_line,
                source=func_source,
                parameters=params,
                calls=calls,
                is_async=self._is_async(node),
                status=ParseStatus.SUPPORTED
            )
            
        except Exception:
            return None
    
    def _extract_class(
        self,
        node: 'Node',
        file_path: Path,
        source: str
    ) -> Optional[ClassInfo]:
        """Extract class information."""
        try:
            # Get class name
            name = None
            for child in node.children:
                if child.type == 'identifier':
                    name = self._get_node_text(child, source)
                    break
            
            if not name:
                return None
            
            class_id = f"{file_path}::{name}"
            
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Get source
            class_source = self._get_node_text(node, source)
            
            # Extract methods
            methods = []
            for child in node.children:
                if child.type == 'class_body':
                    for method_node in child.children:
                        if method_node.type == 'method_definition':
                            for mc in method_node.children:
                                if mc.type == 'property_identifier':
                                    methods.append(self._get_node_text(mc, source))
            
            return ClassInfo(
                id=class_id,
                name=name,
                file=str(file_path),
                start_line=start_line,
                end_line=end_line,
                source=class_source,
                methods=methods,
                status=ParseStatus.SUPPORTED
            )
            
        except Exception:
            return None
    
    def _extract_import(self, node: 'Node', source: str) -> List[str]:
        """Extract import statements."""
        imports = []
        
        try:
            for child in node.children:
                if child.type == 'import_clause':
                    # Named imports
                    for ic in child.children:
                        if ic.type == 'identifier':
                            imports.append(self._get_node_text(ic, source))
                        elif ic.type == 'named_imports':
                            for spec in ic.children:
                                if spec.type == 'import_specifier':
                                    for isc in spec.children:
                                        if isc.type == 'identifier':
                                            imports.append(self._get_node_text(isc, source))
                
                elif child.type == 'string':
                    # Module path
                    module_path = self._get_node_text(child, source).strip('"\'')
                    if module_path and not module_path.startswith('.'):
                        imports.append(module_path)
        
        except Exception:
            pass
        
        return imports
    
    def _extract_parameters(self, node: 'Node', source: str) -> List[str]:
        """Extract function parameters."""
        params = []
        
        for child in node.children:
            if child.type == 'formal_parameters':
                for param in child.children:
                    if param.type in ('identifier', 'required_parameter'):
                        params.append(self._get_node_text(param, source))
        
        return params
    
    def _extract_calls(self, node: 'Node', source: str) -> List[str]:
        """Extract function calls."""
        calls = []
        
        def walk_for_calls(n: 'Node'):
            if n.type == 'call_expression':
                # Get function name
                for child in n.children:
                    if child.type == 'identifier':
                        calls.append(self._get_node_text(child, source))
                        break
                    elif child.type == 'member_expression':
                        # For obj.method() calls
                        call_name = self._get_node_text(child, source)
                        calls.append(call_name)
                        break
            
            for child in n.children:
                walk_for_calls(child)
        
        walk_for_calls(node)
        return calls
    
    def _is_async(self, node: 'Node') -> bool:
        """Check if function is async."""
        for child in node.children:
            if child.type == 'async':
                return True
        return False
    
    def _get_node_text(self, node: 'Node', source: str) -> str:
        """Get text content of a node."""
        return source[node.start_byte:node.end_byte]
