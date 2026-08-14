import json
import os
import logging
from .gemini_client import call_gemini

logger = logging.getLogger("codeoracle.explainer")

def generate_explanations(chunks: list) -> dict:
    """
    Generates high-level repository, module, class, and function-level explanations.
    Conforms to the CONTRACT.md Explanation schema.
    """
    explanation_result = {
        "modules": [],
        "functions": []
    }

    if not chunks:
        return explanation_result

    # 1. Group chunks by file
    files_data = {}
    for chunk in chunks:
        file_path = chunk["file"]
        if file_path not in files_data:
            files_data[file_path] = {
                "module": None,
                "classes": [],
                "functions": [],
                "language": chunk["language"]
            }
        
        if chunk["type"] == "module":
            files_data[file_path]["module"] = chunk
        elif chunk["type"] == "class":
            files_data[file_path]["classes"].append(chunk)
        elif chunk["type"] == "function":
            files_data[file_path]["functions"].append(chunk)

    # 2. Generate Repository Overview
    try:
        repo_metadata = []
        for file_path, data in files_data.items():
            classes = [c["name"] for c in data["classes"]]
            funcs = [f["name"] for f in data["functions"]]
            repo_metadata.append({
                "file": file_path,
                "language": data["language"],
                "classes": classes,
                "functions": funcs
            })

        repo_prompt = (
            f"You are a principal software architect. Review this repository metadata and write a high-level natural language summary of the entire repository.\n"
            f"Include structure, purpose, and general architecture.\n"
            f"Repository file listing and symbols:\n{json.dumps(repo_metadata, indent=2)}\n\n"
            f"Safety Guidelines:\n"
            f"- Ground your explanation strictly on the facts present in the listing.\n"
            f"- If something cannot be determined, explicitly say so.\n"
            f"- Do not hallucinate or invent features/behavior that is not indicated by the file and symbol names."
        )
        sys_instruction = "You are a code documentation engine. Return a clear, concise, and professional repository architecture description."
        repo_summary = call_gemini(repo_prompt, system_instruction=sys_instruction, model_name="gemini-flash-latest")
        
        # Add Repository Overview as a virtual module to satisfy CONTRACT.md cleanly
        explanation_result["modules"].append({
            "file": "Repository Summary",
            "summary": repo_summary.strip()
        })
    except Exception as e:
        logger.error(f"Failed to generate repository summary: {str(e)}")
        explanation_result["modules"].append({
            "file": "Repository Summary",
            "summary": f"Failed to generate repository architecture overview: {str(e)}"
        })

    # 3. Process each file
    for file_path, data in files_data.items():
        language = data["language"]
        module_chunk = data["module"]
        
        # 3.1. Generate Module & Class Explanation
        module_summary = ""
        if module_chunk:
            if "error" in module_chunk:
                module_summary = f"Unparseable file due to syntax issues: {module_chunk['error']}"
            else:
                try:
                    # Truncate source if it's extremely long for safety
                    source_lines = module_chunk["source"].splitlines()
                    source_snippet = "\n".join(source_lines[:400]) # First 400 lines
                    if len(source_lines) > 400:
                        source_snippet += "\n... [TRUNCATED] ..."

                    # Build Class description list to supply as context
                    classes_context = []
                    for cc in data["classes"]:
                        class_lines = cc["source"].splitlines()
                        class_snippet = "\n".join(class_lines[:100])
                        classes_context.append({
                            "name": cc["name"],
                            "source": class_snippet
                        })

                    prompt = (
                        f"Provide a clear, natural language explanation of this code module (file).\n"
                        f"File path: {file_path}\n"
                        f"Language: {language}\n\n"
                        f"Source Code:\n```\n{source_snippet}\n```\n\n"
                        f"Classes declared in this file:\n{json.dumps(classes_context, indent=2)}\n\n"
                        f"Requirements:\n"
                        f"1. Explain the purpose and general logic of the file.\n"
                        f"2. Summarize each class declared inside this file and its main responsibilities.\n"
                        f"3. Strict Hallucination Check: Only state facts visible in the code snippets. Do not make assumptions about external systems unless they are visible in imports or calls."
                    )
                    
                    sys_instruction = "You are a senior software developer writing clear documentation. Return markdown explanations."
                    response = call_gemini(prompt, system_instruction=sys_instruction, model_name="gemini-flash-latest")
                    module_summary = response.strip()
                except Exception as e:
                    module_summary = f"Failed to generate module summary: {str(e)}"
        else:
            module_summary = "No module contents found."

        explanation_result["modules"].append({
            "file": file_path,
            "summary": module_summary
        })

        # 3.2. Generate Function explanations with detailed fields
        func_chunks = data["functions"]
        if not func_chunks:
            continue

        functions_to_explain = []
        for fc in func_chunks:
            # Truncate large functions
            func_lines = fc["source"].splitlines()
            func_source = "\n".join(func_lines[:150])
            if len(func_lines) > 150:
                func_source += "\n... [TRUNCATED] ..."
                
            functions_to_explain.append({
                "name": fc["name"],
                "source": func_source,
                "calls": fc.get("calls", []),
                "imports": fc.get("imports", [])
            })

        if functions_to_explain:
            try:
                prompt = (
                    f"Explain the following functions in the file '{file_path}' (written in {language}).\n"
                    f"Analyze each function signature and body to extract facts. "
                    f"Do not invent any details. If details are not in the code, write 'Cannot be determined from code'.\n\n"
                    f"Functions code list:\n{json.dumps(functions_to_explain, indent=2)}\n\n"
                    f"Return a JSON object with a single root key 'functions' containing a list of objects structured exactly as:\n"
                    f'{{\n'
                    f'  "functions": [\n'
                    f'    {{\n'
                    f'      "name": "function_name",\n'
                    f'      "purpose": "A concise overview of the function\'s main purpose",\n'
                    f'      "inputs": ["Parameter descriptions (name and inferred type)"],\n'
                    f'      "outputs": "Description of return values and types",\n'
                    f'      "logic": ["Step-by-step description of logical flow"],\n'
                    f'      "dependencies": ["Functions called or libraries imported"],\n'
                    f'      "side_effects": ["Mutations, database updates, prints, or \'none\'"],\n'
                    f'      "potential_risks": ["Vulnerabilities, division-by-zero, bounds issues, or \'none\'"]\n'
                    f'    }}\n'
                    f'  ]\n'
                    f'}}'
                )

                sys_instruction = "You are a code analysis bot. Output ONLY valid JSON containing the specified format."
                response_json_str = call_gemini(
                    prompt, 
                    system_instruction=sys_instruction, 
                    json_mode=True, 
                    model_name="gemini-flash-latest"
                )
                
                parsed_res = json.loads(response_json_str)
                for item in parsed_res.get("functions", []):
                    name = item.get("name")
                    
                    # Construct function summary string incorporating all fields requested
                    inputs_list = item.get("inputs", [])
                    logic_list = item.get("logic", [])
                    deps_list = item.get("dependencies", [])
                    side_effects_list = item.get("side_effects", [])
                    risks_list = item.get("potential_risks", [])

                    formatted_summary = (
                        f"**Purpose:** {item.get('purpose', 'N/A')}\n\n"
                        f"**Inputs:**\n" + ("\n".join(f"- {inp}" for inp in inputs_list) if inputs_list else "- None") + "\n\n"
                        f"**Outputs:** {item.get('outputs', 'N/A')}\n\n"
                        f"**Logic Steps:**\n" + ("\n".join(f"- {step}" for step in logic_list) if logic_list else "- None") + "\n\n"
                        f"**Dependencies:**\n" + ("\n".join(f"- {dep}" for dep in deps_list) if deps_list else "- None") + "\n\n"
                        f"**Side Effects:**\n" + ("\n".join(f"- {se}" for se in side_effects_list) if side_effects_list else "- None") + "\n\n"
                        f"**Potential Risks:**\n" + ("\n".join(f"- {risk}" for risk in risks_list) if risks_list else "- None")
                    )

                    # Extract parameter names from chunk metadata if available, otherwise fallback to name list
                    matching_chunk = next((fc for fc in func_chunks if fc["name"] == name), None)
                    params = matching_chunk.get("imports", []) if matching_chunk else [] # fallback parameters

                    explanation_result["functions"].append({
                        "file": file_path,
                        "name": name,
                        "summary": formatted_summary,
                        "params": params,
                        "returns": item.get("outputs", "unknown")
                    })
            except Exception as e:
                logger.error(f"Failed to generate structured explanations for functions in {file_path}: {str(e)}")
                # Graceful fallback: populate list with basic placeholders
                for fc in func_chunks:
                    explanation_result["functions"].append({
                        "file": file_path,
                        "name": fc["name"],
                        "summary": f"**Error:** Failed to generate structured explanation for this function due to Gemini error: {str(e)}",
                        "params": [],
                        "returns": "unknown"
                    })

    return explanation_result
