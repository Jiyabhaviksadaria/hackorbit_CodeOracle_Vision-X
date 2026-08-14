"""
Basic cross-file call resolver.
Resolves function calls to their definition files where unambiguous.
Does NOT attempt research-grade static analysis.
"""
from pathlib import Path
from typing import Dict, List, Optional, Set
from ..models.repository import RepositoryAnalysis, FunctionInfo


class CallResolver:
    """
    Resolves calls like 'calculate_tax' → 'tax.py::calculate_tax'
    when the import evidence is reasonably unambiguous.

    Strategy:
    1. Build a map of symbol_name → [file::symbol_id]
    2. For each function's calls, check if the call name appears
       in the function's import list (or module imports).
    3. If unambiguous (only one definition found), resolve it.
    4. If ambiguous, mark as UNCERTAIN and leave unresolved.

    NEVER invent dependencies.
    """

    def resolve(self, analysis: RepositoryAnalysis) -> None:
        """
        Mutate analysis in-place, adding resolved_calls to each function.
        """
        # Build symbol index: name -> list of qualified IDs
        symbol_index: Dict[str, List[str]] = {}
        for func_id, func in analysis.functions.items():
            name = func.name
            if name not in symbol_index:
                symbol_index[name] = []
            symbol_index[name].append(func_id)

        # Build import index: for each file, which names are imported from where
        # e.g. file "billing.py" imports "calculate_tax" from "tax"
        # module_imports[file_path] = {symbol_name: source_module}
        module_imports: Dict[str, Dict[str, str]] = {}
        for module_id, module in analysis.modules.items():
            file_path = module.file
            module_imports[file_path] = {}
            for imp in module.imports:
                # imp is a module name ("tax") or symbol name ("calculate_tax")
                module_imports[file_path][imp] = imp

        # Resolve calls
        for func_id, func in analysis.functions.items():
            resolved = []
            for call_name in func.calls:
                candidates = symbol_index.get(call_name, [])

                if len(candidates) == 1:
                    # Unambiguous - exactly one definition exists
                    resolved.append(candidates[0])
                elif len(candidates) > 1:
                    # Check if the caller imports one of the candidates' modules
                    file_imports = module_imports.get(func.file, {})
                    matched = []
                    for candidate_id in candidates:
                        candidate_file = analysis.functions[candidate_id].file
                        candidate_module = Path(candidate_file).stem
                        if candidate_module in file_imports:
                            matched.append(candidate_id)

                    if len(matched) == 1:
                        resolved.append(matched[0])
                    elif len(matched) > 1:
                        # Still ambiguous - mark all as uncertain
                        resolved.extend(
                            f"UNCERTAIN:{c}" for c in matched
                        )
                    else:
                        # No import evidence - leave as raw call name
                        resolved.append(call_name)
                else:
                    # Not defined in the repository (stdlib / external dep)
                    resolved.append(call_name)

            func.calls = resolved

        # Populate called_by (reverse map)
        for func_id, func in analysis.functions.items():
            for call in func.calls:
                if call in analysis.functions:
                    analysis.functions[call].called_by.append(func_id)
