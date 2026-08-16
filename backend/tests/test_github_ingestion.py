"""
Tests for GitHub repository ingestion, URL normalization, and cloning error handling.
"""
import pytest
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.app.main import app, validate_and_normalize_github_url, _clone_github_repo


@pytest.fixture
def client():
    return TestClient(app)


class TestGithubUrlNormalization:
    @pytest.mark.parametrize("input_url, expected", [
        ("https://github.com/HARSHIL3431/AWDF", "https://github.com/HARSHIL3431/AWDF.git"),
        ("https://github.com/HARSHIL3431/AWDF/", "https://github.com/HARSHIL3431/AWDF.git"),
        ("https://github.com/HARSHIL3431/AWDF.git", "https://github.com/HARSHIL3431/AWDF.git"),
        ("http://github.com/HARSHIL3431/AWDF", "https://github.com/HARSHIL3431/AWDF.git"),
        ("https://www.github.com/HARSHIL3431/AWDF", "https://github.com/HARSHIL3431/AWDF.git"),
        (" https://github.com/HARSHIL3431/AWDF  ", "https://github.com/HARSHIL3431/AWDF.git"),
        ("https://github.com/facebook/react", "https://github.com/facebook/react.git"),
        ("https://github.com/owner-name/repo_name.js", "https://github.com/owner-name/repo_name.js.git"),
    ])
    def test_valid_github_urls(self, input_url, expected):
        assert validate_and_normalize_github_url(input_url) == expected

    @pytest.mark.parametrize("invalid_url", [
        "",
        "   ",
        None,
        123,
        "https://gitlab.com/owner/repo",
        "https://bitbucket.org/owner/repo",
        "https://github.com",
        "https://github.com/",
        "https://github.com/owner",
        "https://github.com/owner/",
        "ftp://github.com/owner/repo",
        "not a url",
    ])
    def test_invalid_github_urls_raise_value_error(self, invalid_url):
        with pytest.raises(ValueError):
            validate_and_normalize_github_url(invalid_url)


class TestUploadGithubEndpoint:
    def test_upload_valid_github_url_success(self, client):
        with patch("backend.app.main.process_github_job") as mock_process:
            resp = client.post(
                "/api/upload",
                json={"github_url": "https://github.com/HARSHIL3431/AWDF"},
                headers={"Content-Type": "application/json"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data
            assert len(data["job_id"]) > 0

    def test_upload_invalid_url_pattern_rejected_with_400(self, client):
        resp = client.post(
            "/api/upload",
            json={"github_url": "https://notgithub.com/owner/repo"},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        assert "Invalid GitHub repository URL" in resp.json()["detail"]

    def test_upload_empty_url_rejected_with_400(self, client):
        resp = client.post(
            "/api/upload",
            json={"github_url": ""},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400


class TestCloneExecutionAndErrorHandling:
    @pytest.mark.asyncio
    async def test_awdf_repo_clones_successfully(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "awdf_clone"
            await _clone_github_repo("https://github.com/HARSHIL3431/AWDF", target, timeout=60)
            assert (target / "src").exists()
            assert (target / "package.json").exists()

    @pytest.mark.asyncio
    async def test_nonexistent_repo_raises_clean_runtime_error(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "fake_repo"
            with pytest.raises(RuntimeError) as excinfo:
                await _clone_github_repo("https://github.com/HARSHIL3431/non-existent-xyz-99999", target, timeout=10)
            assert "Repository not accessible" in str(excinfo.value)
