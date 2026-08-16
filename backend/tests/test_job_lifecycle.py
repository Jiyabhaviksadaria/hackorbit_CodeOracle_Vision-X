import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.jobs.job_manager import job_manager

client = TestClient(app)

def test_nonexistent_job_status_returns_404_detail():
    """Verify that querying status for an unknown/expired job_id returns 404 with helpful detail."""
    response = client.get("/api/jobs/nonexistent_job_12345/status")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Job not found or expired" in data["detail"]

def test_nonexistent_job_result_returns_404_detail():
    """Verify that querying result for an unknown/expired job_id returns 404 with helpful detail."""
    response = client.get("/api/jobs/nonexistent_job_12345/result")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Job not found or expired" in data["detail"]

def test_job_lifecycle_create_poll_result():
    """Verify complete in-memory job lifecycle from creation to polling to completion."""
    job_id = job_manager.create_job()
    assert job_id is not None

    # Retrieve status
    status_resp = client.get(f"/api/jobs/{job_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "queued"

    # Set completed status
    job_manager.update_status(job_id, "done", progress=100)
    job_manager.set_analysis_data(job_id, {"raw_ast": {}, "explanations": {}})

    # Fetch status when done
    status_resp2 = client.get(f"/api/jobs/{job_id}/status")
    assert status_resp2.status_code == 200
    assert status_resp2.json()["status"] == "done"

    # Fetch result when done
    result_resp = client.get(f"/api/jobs/{job_id}/result")
    assert result_resp.status_code == 200
    res_data = result_resp.json()
    assert "explanation" in res_data
    assert "dependency_graph" in res_data
    assert "tests" in res_data
    assert "refactor" in res_data
