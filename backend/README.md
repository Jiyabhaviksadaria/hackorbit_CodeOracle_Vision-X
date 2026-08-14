# CodeOracle Backend

Backend implementation for CodeOracle - AI-Powered Legacy Codebase Explainer & Modernizer.

## Architecture

The backend provides:
- **ZIP ingestion**: Safe extraction with security checks
- **Language detection**: Deterministic Python + JavaScript detection
- **AST parsing**: Python (stdlib ast) + JavaScript (tree-sitter)
- **Code intelligence**: Functions, classes, modules, imports, calls
- **Job management**: Async processing with status tracking
- **Test execution**: Isolated test running with coverage measurement

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

MAX_UPLOAD_SIZE_MB=100
MAX_LOC=10000
STAGE_TIMEOUT_SECONDS=300
TEMP_WORKSPACE_ROOT=./workspaces
```

## Running

Development server:
```bash
cd backend
python -m app.main
```

Or with uvicorn:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Core Endpoints (LOCKED per CONTRACT.md)

#### Upload Repository
```http
POST /api/upload
Content-Type: multipart/form-data

file: <ZIP file>
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Get Job Status
```http
GET /api/jobs/{job_id}/status
```

Response:
```json
{
  "status": "parsing",
  "progress": 50,
  "error": null
}
```

Status values: `queued`, `parsing`, `explaining`, `testing`, `refactoring`, `done`, `error`

#### Get Job Result
```http
GET /api/jobs/{job_id}/result
```

Response (matches CONTRACT.md):
```json
{
  "explanation": { "modules": [], "functions": [] },
  "dependency_graph": { "nodes": [], "edges": [] },
  "tests": { "test_files": [], "coverage_percent": 0.0, "passed": 0, "failed": 0, "log": "" },
  "refactor": { "files": [] }
}
```

### Debug Endpoints

#### Get Internal Analysis
```http
GET /api/jobs/{job_id}/analysis
```

Returns internal repository analysis details.

## Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Module Structure

```
backend/
├── app/
│   ├── ingestion/          # ZIP handling, language detection
│   ├── parsing/            # Python AST, JavaScript tree-sitter
│   ├── jobs/               # Job management
│   ├── testing/            # Test execution, coverage
│   ├── models/             # Internal + contract models
│   └── main.py             # FastAPI application
└── tests/
    ├── test_contract.py    # Contract validation
    ├── test_ingestion.py   # ZIP handling tests
    └── test_python_parser.py # Parser tests
```

## Owned Modules

Backend Engineer owns:
- `app/ingestion/` - ZIP handling, language detection, file tree
- `app/parsing/` - Python parser, JavaScript parser, repository analyzer
- `app/jobs/` - Job state management
- `app/testing/` - Test runner, coverage measurement
- `app/main.py` - FastAPI application
- `tests/` - Backend tests

**DO NOT MODIFY:**
- `app/ai/` - Owned by AI/ML Engineer
- `app/api/` - Owned by API/Integration Engineer  
- `app/graph/` - Owned by API/Integration Engineer

## Contract Safety

The `ParsedChunk` contract is **LOCKED** per CONTRACT.md. Never change:
- Field names
- Field types
- Required fields
- Semantics

Use `ParsedChunkAdapter` to convert internal models to the contract format.

## Key Features

### Safe ZIP Extraction
- Path traversal protection
- Size limits (configurable)
- Ignored directories (.git, node_modules, etc.)
- Corruption detection

### Deterministic Parsing
- Python: stdlib `ast` module
- JavaScript: `tree-sitter`
- No AI for code structure
- Graceful error handling (one bad file doesn't crash the job)

### Repository Analysis
Internal `RepositoryAnalysis` model provides:
- File tree with metadata
- LOC calculation
- Language detection
- Functions, classes, modules
- Imports and calls
- Cross-file dependencies
- Parse error tracking

### Partial Results
Pipeline stages fail independently:
- Parse errors are recorded but don't stop the job
- Unsupported files are tracked separately
- Other stages can continue with partial data

### Test Execution
- Isolated workspace (never modify original files)
- Subprocess timeout protection
- Python: pytest + coverage.py
- JavaScript: npm test (uses repo's test runner)
- Syntax validation before execution

## Integration Points

### For AI/ML Team
Backend provides `ParsedChunk` list matching CONTRACT.md:
```python
from app.parsing.contract_adapter import ParsedChunkAdapter
from app.models.repository import Language

chunks = ParsedChunkAdapter.from_repository_analysis(
    functions, classes, Language.PYTHON
)
```

### For API/Integration Team
Backend exposes locked endpoints and job state management.

## Known Limitations

1. JavaScript parser requires `tree-sitter-javascript` to be installed
2. No database - jobs are in-memory (lost on restart)
3. No GitHub cloning yet (ZIP only)
4. Simple cross-file resolution (not research-grade static analysis)

## Next Steps

See `MEMORY.md` for current status and next implementation phases.

## License

Part of CodeOracle hackathon project (Hack Orbit 2026, PS-06).
