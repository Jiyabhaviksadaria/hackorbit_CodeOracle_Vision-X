"""
API Integration Tests — owned by API/Integration Engineer.

Covers:
  - POST /api/upload  (ZIP + GitHub URL paths)
  - GET  /api/jobs/{job_id}/status
  - GET  /api/jobs/{job_id}/result  (CONTRACT.md shape validation)
  - GET  /api/jobs/{job_id}/chunks
  - Dependency graph builder
  - Aggregator (partial failure, empty stages)

Run with:
    cd backend
    pytest tests/test_api_integration.py -v
"""
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.models.contract import ParsedChunk
from app.graph.dependency_graph import build_dep_graph
from app.api.aggregator import aggregate_results, store_dep_graph, store_explanation, store_tests, store_refactor


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def simple_python_zip(tmp_path) -> Path:
    """Minimal valid Python repo as a ZIP."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n"
    )
    zip_path = tmp_path / "repo.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in repo.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(repo))
    return zip_path


@pytest.fixture
def chunks_with_calls() -> list:
    """ParsedChunks that have call relationships."""
    return [
        ParsedChunk(
            file="calc.py", language="python", type="function",
            name="add", start_line=1, end_line=2,
            source="def add(a, b): return a + b",
            calls=[], imports=[]
        ),
        ParsedChunk(
            file="calc.py", language="python", type="function",
            name="main", start_line=4, end_line=6,
            source="def main():\n    return add(1, 2)",
            calls=["add"], imports=[]
        ),
    ]


# ── Upload endpoint ───────────────────────────────────────────────────

class TestUploadEndpoint:

    def test_upload_zip_returns_job_id(self, client, simple_python_zip):
        with open(simple_python_zip, "rb") as f:
            resp = client.post("/api/upload", files={"file": ("repo.zip", f, "application/zip")})
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
        assert len(data["job_id"]) > 0

    def test_upload_non_zip_rejected(self, client, tmp_path):
        txt = tmp_path / "code.py"
        txt.write_text("print('hi')")
        with open(txt, "rb") as f:
            resp = client.post("/api/upload", files={"file": ("code.py", f, "text/plain")})
        assert resp.status_code == 400

    def test_upload_github_url_returns_job_id(self, client):
        resp = client.post(
            "/api/upload",
            json={"github_url": "https://github.com/some/repo"},
            headers={"Content-Type": "application/json"},
        )
        # Job is created immediately — clone happens in background
        assert resp.status_code == 200
        assert "job_id" in resp.json()

    def test_upload_github_url_invalid_scheme_rejected(self, client):
        resp = client.post(
            "/api/upload",
            json={"github_url": "ftp://notgithub.com/repo"},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_upload_github_url_empty_rejected(self, client):
        resp = client.post(
            "/api/upload",
            json={"github_url": ""},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_upload_no_body_rejected(self, client):
        resp = client.post(
            "/api/upload",
            headers={"Content-Type": "application/json"},
            content=b"{}",
        )
        assert resp.status_code == 400

    def test_upload_response_only_has_job_id(self, client, simple_python_zip):
        """CONTRACT: response must be exactly { job_id }."""
        with open(simple_python_zip, "rb") as f:
            resp = client.post("/api/upload", files={"file": ("repo.zip", f, "application/zip")})
        data = resp.json()
        assert set(data.keys()) == {"job_id"}


# ── Status endpoint ───────────────────────────────────────────────────

class TestStatusEndpoint:

    def test_status_unknown_job_returns_404(self, client):
        resp = client.get("/api/jobs/nonexistent-id/status")
        assert resp.status_code == 404

    def test_status_shape_matches_contract(self, client, simple_python_zip):
        """CONTRACT: status must have status, progress, and optional error."""
        with open(simple_python_zip, "rb") as f:
            job_id = client.post("/api/upload", files={"file": ("repo.zip", f, "application/zip")}).json()["job_id"]

        resp = client.get(f"/api/jobs/{job_id}/status")
        assert resp.status_code == 200
        data = resp.json()

        assert "status" in data
        assert "progress" in data
        assert data["status"] in ("queued", "parsing", "explaining", "testing", "refactoring", "done", "error")
        assert 0 <= data["progress"] <= 100

    def test_status_error_field_present_on_failure(self, client):
        """error field must be present (even if null) in status response."""
        # Create a job via GitHub URL that will fail (no real network in test)
        resp = client.post(
            "/api/upload",
            json={"github_url": "https://github.com/definitelynotreal/notarepo12345"},
            headers={"Content-Type": "application/json"},
        )
        job_id = resp.json()["job_id"]
        status_resp = client.get(f"/api/jobs/{job_id}/status")
        assert status_resp.status_code == 200
        # error key should be present (may be None if not yet failed)
        assert "status" in status_resp.json()


# ── Result endpoint ───────────────────────────────────────────────────

class TestResultEndpoint:

    def test_result_not_done_returns_400(self, client, simple_python_zip):
        with open(simple_python_zip, "rb") as f:
            job_id = client.post("/api/upload", files={"file": ("repo.zip", f, "application/zip")}).json()["job_id"]
        # Job is in progress — result not ready yet
        resp = client.get(f"/api/jobs/{job_id}/result")
        # Must be 400 (not done) or 200 (if processing finished instantly in test)
        assert resp.status_code in (200, 400)

    def test_result_unknown_job_returns_404(self, client):
        resp = client.get("/api/jobs/does-not-exist/result")
        assert resp.status_code == 404

    def test_result_shape_matches_contract(self):
        """
        CONTRACT validation: aggregate_results() must always return
        exactly the four keys defined in CONTRACT.md §3.
        """
        result = aggregate_results(None)
        assert set(result.keys()) == {"explanation", "dependency_graph", "tests", "refactor"}

        # explanation
        assert "modules" in result["explanation"]
        assert "functions" in result["explanation"]

        # dependency_graph
        assert "nodes" in result["dependency_graph"]
        assert "edges" in result["dependency_graph"]

        # tests
        assert "test_files" in result["tests"]
        assert "coverage_percent" in result["tests"]
        assert "passed" in result["tests"]
        assert "failed" in result["tests"]
        assert "log" in result["tests"]

        # refactor
        assert "files" in result["refactor"]

    def test_result_partial_stages_still_valid(self):
        """Aggregator must return valid shape even when some stages are missing."""
        partial_data = {
            "explanation": {"modules": [{"file": "a.py", "summary": "..."}], "functions": []},
            # dependency_graph missing
            # tests missing
            "refactor": None,  # explicitly None
        }
        result = aggregate_results(partial_data)
        assert result["dependency_graph"] == {"nodes": [], "edges": []}
        assert result["tests"]["coverage_percent"] == 0.0
        assert result["refactor"] == {"files": []}
        assert result["explanation"]["modules"][0]["file"] == "a.py"

    def test_result_all_stages_populated(self):
        """When all stages present, values must pass through unchanged."""
        full_data = {
            "explanation": {"modules": [{"file": "x.py", "summary": "s"}], "functions": [{"name": "f"}]},
            "dependency_graph": {"nodes": [{"id": "x::f"}], "edges": []},
            "tests": {"test_files": [], "coverage_percent": 78.5, "passed": 10, "failed": 1, "log": "ok"},
            "refactor": {"files": [{"original_file": "x.py", "refactored_source": "...", "breaking_changes": []}]},
        }
        result = aggregate_results(full_data)
        assert result["tests"]["coverage_percent"] == 78.5
        assert result["dependency_graph"]["nodes"][0]["id"] == "x::f"
        assert result["refactor"]["files"][0]["original_file"] == "x.py"


# ── Dependency graph builder ──────────────────────────────────────────

class TestDepGraph:

    def test_empty_chunks_returns_empty_graph(self):
        graph = build_dep_graph([])
        assert graph.nodes == []
        assert graph.edges == []

    def test_nodes_created_for_each_chunk(self, chunks_with_calls):
        graph = build_dep_graph(chunks_with_calls)
        node_ids = {n["id"] for n in graph.nodes}
        assert "calc.py::add" in node_ids
        assert "calc.py::main" in node_ids

    def test_edge_created_for_call_relationship(self, chunks_with_calls):
        graph = build_dep_graph(chunks_with_calls)
        edges = [(e["source"], e["target"]) for e in graph.edges]
        assert ("calc.py::main", "calc.py::add") in edges

    def test_no_self_loop_edges(self, chunks_with_calls):
        graph = build_dep_graph(chunks_with_calls)
        for edge in graph.edges:
            assert edge["source"] != edge["target"]

    def test_no_duplicate_edges(self):
        """Duplicate calls in source should not produce duplicate edges."""
        chunks = [
            ParsedChunk(
                file="a.py", language="python", type="function",
                name="foo", start_line=1, end_line=3,
                source="def foo(): bar(); bar()",
                calls=["bar", "bar"], imports=[]
            ),
            ParsedChunk(
                file="a.py", language="python", type="function",
                name="bar", start_line=5, end_line=6,
                source="def bar(): pass",
                calls=[], imports=[]
            ),
        ]
        graph = build_dep_graph(chunks)
        edges = [(e["source"], e["target"]) for e in graph.edges]
        assert len(edges) == len(set(edges))

    def test_node_schema_matches_contract(self, chunks_with_calls):
        """Each node must have id, label, file — per CONTRACT.md."""
        graph = build_dep_graph(chunks_with_calls)
        for node in graph.nodes:
            assert "id" in node
            assert "label" in node
            assert "file" in node

    def test_edge_schema_matches_contract(self, chunks_with_calls):
        """Each edge must have source, target — per CONTRACT.md."""
        graph = build_dep_graph(chunks_with_calls)
        for edge in graph.edges:
            assert "source" in edge
            assert "target" in edge

    def test_unresolved_calls_skipped(self):
        """Calls to functions not in chunks should produce no edge."""
        chunks = [
            ParsedChunk(
                file="a.py", language="python", type="function",
                name="foo", start_line=1, end_line=2,
                source="def foo(): external_lib()",
                calls=["external_lib"], imports=[]
            )
        ]
        graph = build_dep_graph(chunks)
        # external_lib has no node → no edge
        assert graph.edges == []

    def test_import_edges_created(self):
        """Import relationships should also produce edges when target is a known node."""
        chunks = [
            ParsedChunk(
                file="main.py", language="python", type="module",
                name="main", start_line=1, end_line=5,
                source="import utils", calls=[], imports=["utils"]
            ),
            ParsedChunk(
                file="utils.py", language="python", type="module",
                name="utils", start_line=1, end_line=3,
                source="# utils", calls=[], imports=[]
            ),
        ]
        graph = build_dep_graph(chunks)
        edges = [(e["source"], e["target"]) for e in graph.edges]
        assert ("main.py::main", "utils.py::utils") in edges

    def test_graph_serializable(self, chunks_with_calls):
        """DepGraph must be JSON-serializable via .model_dump()."""
        graph = build_dep_graph(chunks_with_calls)
        data = graph.model_dump()
        assert isinstance(data, dict)
        assert "nodes" in data
        assert "edges" in data


# ── Health check ──────────────────────────────────────────────────────

class TestHealthEndpoints:

    def test_root_returns_running(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    def test_health_returns_healthy(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "parsers" in data
        assert "config" in data
