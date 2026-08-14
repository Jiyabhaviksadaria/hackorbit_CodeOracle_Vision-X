import ast
import os

def parse_python_source_to_chunks(name: str, source: str) -> list:
    """
    Benchmark-only lightweight parser adapter.
    Parses a python source string using stdlib ast and returns a list of ParsedChunk dicts.
    Used exclusively for AI self-contained benchmark evaluation fixtures.
    """
    lines = source.splitlines()
    loc = len(lines)
    
    try:
        tree = ast.parse(source, filename=name)
    except SyntaxError as se:
        return [{
            "file": name,
            "language": "python",
            "type": "module",
            "name": name,
            "start_line": 1,
            "end_line": max(1, loc),
            "source": source,
            "calls": [],
            "imports": [],
            "error": f"SyntaxError: {se.msg} on line {se.lineno}"
        }]

    chunks = []
    
    # Extract module level imports
    module_imports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                module_imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for n in node.names:
                module_imports.append(f"{mod}.{n.name}" if mod else n.name)

    def find_calls(node_body):
        calls = []
        for child in ast.walk(node_body):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name):
                    calls.append(func.id)
                elif isinstance(func, ast.Attribute):
                    calls.append(func.attr)
        return list(set(calls))

    def get_source(start_line, end_line):
        return "\n".join(lines[start_line - 1 : end_line])

    chunks.append({
        "file": name,
        "language": "python",
        "type": "module",
        "name": name,
        "start_line": 1,
        "end_line": max(1, loc),
        "source": source,
        "calls": find_calls(tree),
        "imports": list(set(module_imports))
    })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            func_imports = []
            for child in ast.walk(node):
                if isinstance(child, ast.Import):
                    for n in child.names:
                        func_imports.append(n.name)
                elif isinstance(child, ast.ImportFrom):
                    mod = child.module or ""
                    for n in child.names:
                        func_imports.append(f"{mod}.{n.name}" if mod else n.name)

            chunks.append({
                "file": name,
                "language": "python",
                "type": "function",
                "name": node.name,
                "start_line": start,
                "end_line": end,
                "source": get_source(start, end),
                "calls": find_calls(node),
                "imports": list(set(func_imports))
            })
            
        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            chunks.append({
                "file": name,
                "language": "python",
                "type": "class",
                "name": node.name,
                "start_line": start,
                "end_line": end,
                "source": get_source(start, end),
                "calls": find_calls(node),
                "imports": []
            })
            
    return chunks
