# AI/ML Integration Notes — CodeOracle

This document details the upgrades, architecture, and integration details for the AI intelligence layer in CodeOracle.

## 1. Architecture & AI Adapter Boundary

Following the principle **"Backend owns infrastructure; AI owns intelligence"**, the AI layer consumes authoritative Backend infrastructure through a thin adapter layer located in `backend/app/ai/adapters/`:

- `test_runner_adapter.py`: Wraps the Backend Engineer's `TestRunner` class (`backend.app.testing.test_runner`). Translates AI module parameters (`repo_dir`, `test_files`, `language`) into workspace creation, test execution, coverage measurement, and cleanup via `TestRunner`.
- `parser_adapter.py`: Provides lightweight Python `ast` chunk extraction for self-contained AI benchmark evaluation (`benchmark.py`).

No AI module directly executes subprocess commands, creates test workspaces, or maintains duplicate parsers.

---

## 2. API Contract & Schema Compliance

The AI/ML output matches the `CONTRACT.md` schema with backward-compatible expansions:

### A. Explanations (`explainer.py`)
- **Repository Overview**: Appended as a virtual file `"Repository Summary"` inside the `modules` array.
- **Class Summaries**: Written directly into their respective file descriptions.
- **Function Summaries**: Organized in a structured markdown format inside the `"summary"` string:
  ```text
  **Purpose:** Description...
  **Inputs:** Param details...
  **Outputs:** Return details...
  **Logic Steps:** Descriptions...
  **Dependencies:** Functions called...
  **Side Effects:** State changes...
  **Potential Risks:** Security / exception risks...
  ```

### B. Test Suites (`test_gen.py`)
- Employs an active test execution and coverage feedback loop via Backend's `TestRunner` (pytest for Python, Jest for JS).
- Merges additional tests if coverage is <70%.
- Attempts syntax/import repairs if compilation fails (maximum of 2 iterations).
- Expands response payload with telemetry keys (`initial_coverage`, `iterations_used`).

### C. Refactoring Safety (`refactor.py`)
- Uses deterministic AST signature comparisons (via Python `ast` and tree-sitter JS) to check for:
  - Renamed / removed functions.
  - Parameter additions, removals, and order changes.
  - Required parameters added without default values.
- Combines static checks with Gemini semantic analysis to assign risk levels: `SAFE`, `LOW`, `MEDIUM`, `HIGH`, `VALIDATION FAILED`.
- Prepends warnings in `breaking_changes` list as `[RISK_LEVEL] Message...`.

---

## 3. Gemini Client Telemetry

The client (`gemini_client.py`) collects performance metrics in a `GeminiTelemetry` instance:
- `total_calls`: total API requests made.
- `successful_calls`: successful responses.
- `failed_calls`: failed attempts after retries.
- `retries`: retry attempts triggered by rate-limits or connection errors.
- `total_processing_time`: cumulative response latency.

Telemetry dict is serialized inside the benchmark output logs.

---

## 4. Verification & Testing

### Unit Tests
Run unit tests for AI logic from the root folder:
```bash
python -m pytest backend/app/tests/test_ai_modules.py -v
```

### Real Backend Integration Tests
Run real end-to-end integration tests combining Backend's `RepositoryAnalyzer`, `ParsedChunkAdapter`, AI layer, and Backend `TestRunner`:
```bash
python -m pytest backend/app/tests/test_real_integration.py -v
```

### AI Evaluation Benchmark
To run the automated LLM-as-a-judge benchmark, execute:
```bash
python backend/app/ai/evaluation/benchmark.py
```
This evaluates explanations against reference fact sheets and saves results to `backend/app/ai/evaluation/results.json`.
