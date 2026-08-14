import os
import json
import ast
import shutil
import tempfile
import logging
from tree_sitter_languages import get_parser
from .gemini_client import call_gemini
from .adapters.test_runner_adapter import run_tests_and_measure_coverage

logger = logging.getLogger("codeoracle.refactor")

# --- Python AST Signature Extractor ---
def get_python_signatures(source: str) -> dict:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    signatures = {}

    class SignatureVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            self.add_signature(node, None)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.add_signature(node, None)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            for body_node in node.body:
                if isinstance(body_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.add_signature(body_node, node.name)
            self.generic_visit(node)

        def add_signature(self, node, class_name):
            func_key = f"{class_name}.{node.name}" if class_name else node.name
            args = node.args
            
            # Positional arguments details
            pos_args = []
            defaults_count = len(args.defaults)
            arg_names = [arg.arg for arg in args.args]
            
            for idx, name in enumerate(arg_names):
                # The last N arguments have default values
                has_default = idx >= (len(arg_names) - defaults_count)
                pos_args.append({"name": name, "has_default": has_default})

            # Keyword-only arguments details
            kwonly_args = []
            for idx, arg in enumerate(args.kwonlyargs):
                has_default = args.kw_defaults[idx] is not None
                kwonly_args.append({"name": arg.arg, "has_default": has_default})

            signatures[func_key] = {
                "args": pos_args,
                "kwonlyargs": kwonly_args,
                "vararg": args.vararg is not None,
                "kwarg": args.kwarg is not None
            }

    SignatureVisitor().visit(tree)
    return signatures


# --- Tree-sitter JS Signature Extractor ---
def get_js_signatures(source: str) -> dict:
    try:
        parser = get_parser("javascript")
        tree = parser.parse(bytes(source, "utf8"))
    except Exception:
        return None

    signatures = {}

    def get_node_text(node):
        return node.text.decode("utf-8", errors="ignore")

    def parse_params(formal_params_node):
        params = []
        if not formal_params_node:
            return params
        for child in formal_params_node.children:
            if child.type == "identifier":
                params.append({"name": get_node_text(child), "has_default": False})
            elif child.type == "assignment_pattern":
                id_node = child.children[0]
                params.append({"name": get_node_text(id_node), "has_default": True})
            elif child.type == "rest_parameter":
                id_node = child.children[1] if len(child.children) > 1 else child
                params.append({"name": get_node_text(id_node), "has_default": True})
        return params

    def traverse(node, class_name=None):
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            if name_node:
                func_name = get_node_text(name_node)
                func_key = f"{class_name}.{func_name}" if class_name else func_name
                signatures[func_key] = {"args": parse_params(params_node)}
                
        elif node.type == "method_definition":
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            if name_node:
                func_name = get_node_text(name_node)
                func_key = f"{class_name}.{func_name}" if class_name else func_name
                signatures[func_key] = {"args": parse_params(params_node)}
                
        elif node.type in ("lexical_declaration", "variable_declaration"):
            for declarator in node.children:
                if declarator.type == "variable_declarator":
                    value_node = declarator.child_by_field_name("value")
                    if value_node and value_node.type in ("arrow_function", "function_expression"):
                        name_node = declarator.child_by_field_name("id")
                        params_node = value_node.child_by_field_name("parameters")
                        if name_node:
                            func_name = get_node_text(name_node)
                            func_key = f"{class_name}.{func_name}" if class_name else func_name
                            signatures[func_key] = {"args": parse_params(params_node)}

        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                class_name = get_node_text(name_node)

        for child in node.children:
            traverse(child, class_name)

    traverse(tree.root_node)
    return signatures


# --- Deterministic AST Comparison ---
def compare_signatures(orig_sig: dict, refact_sig: dict) -> list:
    warnings = []
    
    if orig_sig is None or refact_sig is None:
        return ["Structural comparison failed due to syntax error in source files."]

    # Check for removed / renamed functions
    for func_name in orig_sig:
        if func_name not in refact_sig:
            warnings.append(f"Function/Method '{func_name}' was removed or renamed.")
            continue
            
        orig_func = orig_sig[func_name]
        refact_func = refact_sig[func_name]
        
        orig_args = orig_func.get("args", [])
        refact_args = refact_func.get("args", [])
        
        # Check removed parameters
        refact_arg_names = [arg["name"] for arg in refact_args]
        for arg in orig_args:
            if arg["name"] not in refact_arg_names:
                warnings.append(f"Parameter '{arg['name']}' was removed from function '{func_name}'.")
                
        # Check added required parameters
        orig_arg_names = [arg["name"] for arg in orig_args]
        for arg in refact_args:
            if arg["name"] not in orig_arg_names and not arg["has_default"]:
                warnings.append(f"Required parameter '{arg['name']}' was added to function '{func_name}' without a default value.")
            elif arg["name"] not in orig_arg_names and arg["has_default"]:
                warnings.append(f"Optional parameter '{arg['name']}' was added to function '{func_name}'.")

        # Check parameter order changes
        common_args = [arg["name"] for arg in orig_args if arg["name"] in refact_arg_names]
        refact_common_args = [arg["name"] for arg in refact_args if arg["name"] in orig_arg_names]
        if common_args != refact_common_args:
            warnings.append(f"Parameter order of function '{func_name}' was changed.")
            
    return warnings


# --- Refactor Generator & Validator ---
def generate_refactored_code(chunks: list, repo_dir: str = None) -> dict:
    """
    Generates modernized code, conducts deterministic AST-based breaking-change checks,
    and runs behavior validation inside an isolated temporary directory.
    Conforms to the CONTRACT.md RefactorResult schema.
    """
    refactor_result = {
        "files": []
    }

    if not chunks:
        return refactor_result

    # Group chunks by file
    files_data = {}
    for chunk in chunks:
        file_path = chunk["file"]
        if file_path not in files_data:
            files_data[file_path] = {
                "module": None,
                "functions": [],
                "classes": [],
                "language": chunk["language"]
            }
        
        if chunk["type"] == "module":
            files_data[file_path]["module"] = chunk
        elif chunk["type"] == "class":
            files_data[file_path]["classes"].append(chunk)
        elif chunk["type"] == "function":
            files_data[file_path]["functions"].append(chunk)

    for file_path, data in files_data.items():
        language = data["language"]
        module_chunk = data["module"]
        if module_chunk:
            if "error" in module_chunk:
                continue
            original_source = module_chunk["source"]
        else:
            fn_sources = [f["source"] for f in data.get("functions", [])]
            cls_sources = [c["source"] for c in data.get("classes", [])]
            original_source = "\n\n".join(fn_sources + cls_sources)

        if not original_source.strip():
            continue

        # 1. Ask Gemini to generate refactored code
        source_lines = original_source.splitlines()
        source_snippet = "\n".join(source_lines[:400])
        if len(source_lines) > 400:
            source_snippet += "\n... [TRUNCATED] ..."

        refactored_source = original_source
        breaking_changes = []
        risk_level = "SAFE"

        try:
            prompt = (
                f"You are a principal refactoring engineer. Modernize this code file '{file_path}' ({language}).\n\n"
                f"Original Source Code:\n```\n{source_snippet}\n```\n\n"
                f"Requirements:\n"
                f"1. Modernize logic and syntax without changing core behavior (e.g. use PEP 8, async/await, type hints in Python; modern ES6+ in JS).\n"
                f"2. Keep stylistic changes focused. Do not rewrite code arbitrarily.\n"
                f"3. Return a JSON object with: \n"
                f"   - 'refactored_source': The complete modernized code as a string.\n"
                f"   - 'semantic_notes': String describing refactoring approach."
            )
            sys_instruction = "You are a code refactoring tool. Output ONLY JSON."
            response_json_str = call_gemini(
                prompt,
                system_instruction=sys_instruction,
                json_mode=True,
                model_name="gemini-flash-latest"
            )
            
            refactored_source = json.loads(response_json_str).get("refactored_source", original_source)
        except Exception as e:
            logger.error(f"Refactoring generation failed for {file_path}: {str(e)}")
            refactor_result["files"].append({
                "original_file": file_path,
                "refactored_source": original_source,
                "breaking_changes": [f"Refactor engine failure: {str(e)}"]
            })
            continue

        # 2. Syntax Validation check
        syntax_valid = True
        if language == "python":
            try:
                ast.parse(refactored_source)
            except SyntaxError as se:
                syntax_valid = False
                risk_level = "VALIDATION FAILED"
                breaking_changes.append(f"SyntaxError in refactored code: {se.msg} on line {se.lineno}")
        else:
            try:
                parser = get_parser("javascript")
                tree = parser.parse(bytes(refactored_source, "utf8"))
                if tree.root_node.has_error:
                    # Let's count it as warning or syntax issue
                    logger.warning("Tree-sitter detected error nodes in refactored JS")
            except Exception:
                syntax_valid = False
                risk_level = "VALIDATION FAILED"
                breaking_changes.append("Parsing error in refactored JavaScript code.")

        if syntax_valid:
            # 3. Deterministic AST Signature Comparison
            if language == "python":
                orig_sig = get_python_signatures(original_source)
                refact_sig = get_python_signatures(refactored_source)
            else:
                orig_sig = get_js_signatures(original_source)
                refact_sig = get_js_signatures(refactored_source)
                
            ast_warnings = compare_signatures(orig_sig, refact_sig)
            breaking_changes.extend(ast_warnings)

            # 4. Gemini Semantic Analysis of Breaking Changes
            if breaking_changes:
                risk_level = "HIGH"  # Structurally broken signatures
                try:
                    semantic_prompt = (
                        f"Review the following structural changes detected between original and refactored code.\n"
                        f"Provide a risk analysis explaining why these changes might break callers, and classify the risk level "
                        f"as SAFE, LOW, MEDIUM, or HIGH.\n\n"
                        f"Original file: {file_path}\n"
                        f"Structural changes detected:\n{json.dumps(breaking_changes, indent=2)}\n\n"
                        f"Return a JSON object structured as:\n"
                        f'{{"risk_level": "HIGH", "analysis": "detailed explanation"}}'
                    )
                    semantic_res = call_gemini(semantic_prompt, system_instruction="You are a code risk assessor. Output ONLY JSON.", json_mode=True)
                    res_data = json.loads(semantic_res)
                    risk_level = res_data.get("risk_level", "HIGH")
                    analysis_note = res_data.get("analysis", "")
                    if analysis_note:
                        breaking_changes.append(f"Semantic Risk Analysis: {analysis_note}")
                except Exception as e:
                    logger.error(f"Semantic risk analysis failed: {str(e)}")
            else:
                risk_level = "SAFE"

            # 5. Isolated Behavior Validation (running tests on refactored code)
            if repo_dir and syntax_valid:
                # Create an isolated temporary workspace for validation
                with tempfile.TemporaryDirectory() as temp_val_dir:
                    isolated_repo_dir = os.path.join(temp_val_dir, "repo")
                    os.makedirs(isolated_repo_dir)
                    
                    try:
                        # Copy original workspace files
                        # We copy tree recursively, skipping nodes if they are temp files or dirs
                        for item in os.listdir(repo_dir):
                            s = os.path.join(repo_dir, item)
                            d = os.path.join(isolated_repo_dir, item)
                            if os.path.isdir(s):
                                if item not in (".git", "node_modules", "venv", ".venv", "__pycache__"):
                                    shutil.copytree(s, d)
                            else:
                                if not item.endswith((".zip", ".db")):
                                    shutil.copy2(s, d)
                        
                        # Replace target original file with refactored code in the isolated workspace
                        target_val_file = os.path.join(isolated_repo_dir, file_path)
                        os.makedirs(os.path.dirname(target_val_file), exist_ok=True)
                        with open(target_val_file, "w", encoding="utf-8") as f:
                            f.write(refactored_source)

                        # Write dummy generated test file (if it doesn't already exist or if we want to run tests)
                        # We search for any test files in repo_dir and copy them too
                        # Let's run a test execution in the isolated workspace
                        # We retrieve existing test names in repo_dir
                        test_files_payload = []
                        for root, _, files in os.walk(repo_dir):
                            for f in files:
                                if f.startswith("test_") or f.endswith(".test.js"):
                                    rel = os.path.relpath(os.path.join(root, f), repo_dir)
                                    with open(os.path.join(root, f), "r", errors="ignore") as tf:
                                        test_files_payload.append({"file": rel, "source": tf.read()})

                        if test_files_payload:
                            run_res = run_tests_and_measure_coverage(isolated_repo_dir, test_files_payload, language)
                            failed_count = run_res.get("failed", 0)
                            run_log = run_res.get("log", "")
                            
                            if failed_count > 0:
                                # Validation failed because tests broke!
                                risk_level = "HIGH"
                                breaking_changes.append(f"Behavior Validation Failed: Refactored code broke existing unit tests. Failed test logs:\n{run_log}")
                    except Exception as val_err:
                        logger.error(f"Behavior validation execution failed: {str(val_err)}")
                        breaking_changes.append(f"Behavior Validation Error: Failed to execute validation tests: {str(val_err)}")
                        risk_level = "HIGH"

        # 6. Format output warnings matching requirements
        final_warnings = [f"[{risk_level}] {warning}" for warning in breaking_changes]
        if not final_warnings:
            final_warnings = [f"[{risk_level}] No breaking changes detected."]

        refactor_result["files"].append({
            "original_file": file_path,
            "refactored_source": refactored_source,
            "breaking_changes": final_warnings
        })

    return refactor_result
