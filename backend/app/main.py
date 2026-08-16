"""
CodeOracle Backend - Main FastAPI application.
Owned by Backend Engineer.
"""
import os
import re
import subprocess
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio
from typing import List, Dict, Optional

from .models.contract import JobStatus, ParsedChunk
from .jobs.job_manager import job_manager
from .ingestion.zip_handler import (
    extract_zip, create_workspace, cleanup_workspace,
    ZipValidationError, ZipSecurityError
)
from .parsing.repository_analyzer import RepositoryAnalyzer
from .parsing.contract_adapter import ParsedChunkAdapter
from .models.repository import Language
from .graph.dependency_graph import build_dep_graph
from .api.aggregator import aggregate_results, store_dep_graph, store_explanation, store_tests, store_refactor

# Load environment variables
load_dotenv()

# Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
MAX_LOC = int(os.getenv("MAX_LOC", "10000"))
STAGE_TIMEOUT_SECONDS = int(os.getenv("STAGE_TIMEOUT_SECONDS", "300"))
TEMP_WORKSPACE_ROOT = Path(os.getenv("TEMP_WORKSPACE_ROOT", "./workspaces"))

# Ensure workspace root exists
TEMP_WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="CodeOracle Backend",
    description="AI-Powered Legacy Codebase Explainer & Modernizer - Backend API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer
repository_analyzer = RepositoryAnalyzer()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "CodeOracle Backend",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "parsers": {
            "python": True,
            "javascript": repository_analyzer.js_parser is not None
        },
        "config": {
            "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
            "max_loc": MAX_LOC,
            "stage_timeout_seconds": STAGE_TIMEOUT_SECONDS
        }
    }


GITHUB_URL_REGEX = re.compile(
    r"^https?://(www\.)?github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def validate_and_normalize_github_url(url: str) -> str:
    """
    Validates and normalizes a GitHub repository URL.
    Returns standard HTTPS clone URL: https://github.com/owner/repo.git
    Raises ValueError if invalid.
    """
    if not url or not isinstance(url, str):
        raise ValueError("github_url must be a non-empty string.")

    clean_url = url.strip()
    match = GITHUB_URL_REGEX.match(clean_url)
    if not match:
        raise ValueError(
            f"Invalid GitHub repository URL '{clean_url}'. "
            "Expected format: https://github.com/owner/repository"
        )

    owner = match.group("owner")
    repo = match.group("repo")
    return f"https://github.com/{owner}/{repo}.git"


async def _clone_github_repo(github_url: str, target_dir: Path, timeout: int = 120) -> None:
    """
    Clone a public GitHub repo into target_dir.
    Raises RuntimeError with a user-friendly message on failure.
    """
    clean_url = validate_and_normalize_github_url(github_url)

    # Explicitly suppress interactive terminal credential prompts in non-interactive/headless environments
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = ""

    # Ensure parent directory exists and clean target_dir if already exists
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)

    cmd = [
        "git",
        "-c", "core.askPass=",
        "-c", "credential.helper=",
        "clone",
        "--depth=1",
        "--single-branch",
        clean_url,
        str(target_dir),
    ]

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            ),
            timeout=timeout,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()
            if any(term in err.lower() for term in ["not found", "authentication failed", "could not read username", "terminal prompts disabled"]):
                raise RuntimeError(
                    f"Repository not accessible — check that '{github_url}' is public and spelled correctly. ({err[:250]})"
                )
            raise RuntimeError(f"git clone failed: {err[:400]}")
    except asyncio.TimeoutError:
        raise RuntimeError(f"git clone timed out after {timeout}s")
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(f"Failed to execute git clone: {e}")


async def process_github_job(job_id: str, github_url: str):
    """Background task: clone a GitHub repo then run the same analysis pipeline."""
    try:
        job_manager.update_status(job_id, "parsing", progress=5)

        workspace_dir, original_dir, working_dir, generated_tests_dir = create_workspace(
            job_id, TEMP_WORKSPACE_ROOT
        )
        job_manager.set_workspace(job_id, workspace_dir, original_dir, working_dir, generated_tests_dir)

        try:
            await _clone_github_repo(github_url, original_dir, timeout=120)
        except RuntimeError as e:
            job_manager.set_error(job_id, "ingestion", str(e))
            job_manager.update_status(job_id, "error", progress=0, error=str(e))
            return

        job_manager.update_status(job_id, "parsing", progress=30)
        await _run_analysis(job_id, original_dir)

    except Exception as e:
        job_manager.update_status(job_id, "error", progress=0, error=f"Job failed: {e}")


async def _run_analysis(job_id: str, source_dir: Path):
    """
    Shared analysis pipeline used by both ZIP and GitHub paths.
    Runs parse → dep graph → marks done.
    """
    try:
        async with asyncio.timeout(STAGE_TIMEOUT_SECONDS):
            analysis = await asyncio.to_thread(
                repository_analyzer.analyze, source_dir, f"repo_{job_id}"
            )

        if analysis.total_loc > MAX_LOC:
            error_msg = f"Repository too large: {analysis.total_loc} LOC > {MAX_LOC} LOC"
            job_manager.set_error(job_id, "parse", error_msg)
            job_manager.update_status(job_id, "error", progress=0, error=error_msg)
            return

        job_manager.set_repository_info(
            job_id,
            analysis.repository_id,
            analysis.name,
            len(analysis.files),
            len(analysis.supported_files),
            analysis.total_loc,
        )

        success_count = len(analysis.supported_files) - len(analysis.parse_errors)
        job_manager.set_parse_results(job_id, success_count, len(analysis.parse_errors))

        analysis_dict: Dict = {
            "repository_id": analysis.repository_id,
            "name": analysis.name,
            "total_loc": analysis.total_loc,
            "languages": [lang.value for lang in analysis.languages],
            "files": len(analysis.files),
            "supported_files": len(analysis.supported_files),
            "functions": len(analysis.functions),
            "classes": len(analysis.classes),
            "modules": len(analysis.modules),
            "parse_errors": len(analysis.parse_errors),
            "_analysis_obj": analysis,
        }
        job_manager.set_analysis_data(job_id, analysis_dict)

        job_manager.update_status(job_id, "parsing", progress=70)

        # ── Phase 4: Dependency graph (API/Integration) ──────────────
        try:
            chunks = _extract_chunks(analysis)
            dep_graph = build_dep_graph(chunks)
            store_dep_graph(analysis_dict, dep_graph.model_dump())
            job_manager.update_status(job_id, "parsing", progress=85)
        except Exception as e:
            job_manager.set_error(job_id, "parse", f"Dep graph error: {e}")
            chunks = []  # ensure chunks is defined for downstream stages

        # ── Phase 3: AI stages — run concurrently for speed ──────────
        from .ai.explainer import generate_explanation
        from .ai.test_gen import generate_tests
        from .ai.refactor import generate_refactor

        job_manager.update_status(job_id, "explaining", progress=87)

        async def _run_explanation():
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(generate_explanation, chunks),
                    timeout=STAGE_TIMEOUT_SECONDS,
                )
                store_explanation(analysis_dict, result)
            except asyncio.TimeoutError:
                job_manager.set_error(job_id, "ai", "Explanation timed out")
            except Exception as e:
                job_manager.set_error(job_id, "ai", f"Explanation error: {e}")

        async def _run_tests():
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(generate_tests, chunks, str(source_dir)),
                    timeout=STAGE_TIMEOUT_SECONDS,
                )
                store_tests(analysis_dict, result)
            except asyncio.TimeoutError:
                job_manager.set_error(job_id, "test", "Test generation timed out")
            except Exception as e:
                job_manager.set_error(job_id, "test", f"Test generation error: {e}")

        async def _run_refactor():
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(generate_refactor, chunks),
                    timeout=STAGE_TIMEOUT_SECONDS,
                )
                store_refactor(analysis_dict, result)
            except asyncio.TimeoutError:
                job_manager.set_error(job_id, "ai", "Refactor timed out")
            except Exception as e:
                job_manager.set_error(job_id, "ai", f"Refactor error: {e}")

        # All three AI stages run in parallel — max wait = 1× timeout, not 3×
        await asyncio.gather(_run_explanation(), _run_tests(), _run_refactor())

        job_manager.update_status(job_id, "done", progress=100)

    except asyncio.TimeoutError:
        error_msg = f"Repository analysis timeout after {STAGE_TIMEOUT_SECONDS}s"
        job_manager.set_error(job_id, "parse", error_msg)
        job_manager.update_status(job_id, "error", progress=0, error=error_msg)
    except Exception as e:
        job_manager.set_error(job_id, "parse", str(e))
        job_manager.update_status(job_id, "error", progress=0, error=f"Parse error: {e}")


def _extract_chunks(analysis) -> List[ParsedChunk]:
    """
    Convert RepositoryAnalysis → List[ParsedChunk].
    Fixes the broken lang-filter from the original /chunks endpoint.
    """
    lang_map = {
        ".py":  Language.PYTHON,
        ".js":  Language.JAVASCRIPT,
        ".jsx": Language.JAVASCRIPT,
        ".ts":  Language.JAVASCRIPT,
        ".tsx": Language.JAVASCRIPT,
    }
    chunks: List[ParsedChunk] = []
    for lang in analysis.languages:
        lang_functions = [
            f for f in analysis.functions.values()
            if lang_map.get(Path(f.file).suffix) == lang
        ]
        lang_classes = [
            c for c in analysis.classes.values()
            if lang_map.get(Path(c.file).suffix) == lang
        ]
        chunks.extend(
            ParsedChunkAdapter.from_repository_analysis(lang_functions, lang_classes, lang)
        )
    return chunks


async def process_repository_job(job_id: str, zip_path: Path):
    """Background task: extract ZIP then run shared analysis pipeline."""
    try:
        job_manager.update_status(job_id, "parsing", progress=10)

        workspace_dir, original_dir, working_dir, generated_tests_dir = create_workspace(
            job_id, TEMP_WORKSPACE_ROOT
        )
        job_manager.set_workspace(job_id, workspace_dir, original_dir, working_dir, generated_tests_dir)

        try:
            async with asyncio.timeout(STAGE_TIMEOUT_SECONDS):
                await asyncio.to_thread(
                    extract_zip, zip_path, original_dir, max_size_mb=MAX_UPLOAD_SIZE_MB
                )
        except asyncio.TimeoutError:
            error_msg = f"ZIP extraction timeout after {STAGE_TIMEOUT_SECONDS}s"
            job_manager.set_error(job_id, "ingestion", error_msg)
            job_manager.update_status(job_id, "error", progress=0, error=error_msg)
            return
        except (ZipValidationError, ZipSecurityError) as e:
            job_manager.set_error(job_id, "ingestion", str(e))
            job_manager.update_status(job_id, "error", progress=0, error=str(e))
            return

        job_manager.update_status(job_id, "parsing", progress=30)
        await _run_analysis(job_id, original_dir)

    except Exception as e:
        job_manager.update_status(job_id, "error", progress=0, error=f"Job failed: {e}")

    finally:
        if zip_path.exists():
            try:
                zip_path.unlink()
            except Exception:
                pass


@app.post("/api/upload")
async def upload_repository(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
):
    """
    Upload a repository for analysis.

    Accepts either:
      - multipart/form-data with a 'file' field (ZIP)
      - application/json with { "github_url": "<url>" }

    Returns: { job_id: string }  — LOCKED contract (CONTRACT.md §2).
    """
    content_type = request.headers.get("content-type", "")

    # ── JSON body path: GitHub URL ────────────────────────────────────
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        raw_url: Optional[str] = body.get("github_url")
        if not raw_url or not str(raw_url).strip():
            raise HTTPException(status_code=400, detail="github_url is required")

        try:
            clean_github_url = validate_and_normalize_github_url(raw_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        job_id = job_manager.create_job()
        background_tasks.add_task(process_github_job, job_id, clean_github_url)
        return {"job_id": job_id}

    # ── Multipart path: ZIP upload ────────────────────────────────────
    if file is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either a ZIP file (multipart) or { github_url } (JSON)",
        )

    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    job_id = job_manager.create_job()
    temp_zip = TEMP_WORKSPACE_ROOT / f"upload_{job_id}.zip"

    try:
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {size_mb:.1f}MB > {MAX_UPLOAD_SIZE_MB}MB",
            )
        temp_zip.write_bytes(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    background_tasks.add_task(process_repository_job, job_id, temp_zip)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str) -> JobStatus:
    """
    Get job status.
    
    This endpoint is part of the LOCKED contract (CONTRACT.md §2).
    Returns only the public status fields.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or expired. Please start a new analysis."
        )
    
    # Return LOCKED contract status
    return JobStatus(
        status=job.status,
        progress=job.progress,
        error=job.error
    )


@app.get("/api/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """
    Get job result — LOCKED contract (CONTRACT.md §2).

    Always returns all 4 keys. Stages that failed or haven't run yet
    return their empty-but-valid schema defaults.
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or expired. Please start a new analysis."
        )

    if job.status != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Job not done yet. Status: {job.status}"
        )

    return aggregate_results(job.analysis_data)


@app.get("/api/jobs/{job_id}/analysis")
async def get_job_analysis(job_id: str):
    """
    Get internal repository analysis details.
    This is a backend-internal endpoint for debugging/integration.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or expired. Please start a new analysis."
        )
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "repository_name": job.repository_name,
        "total_files": job.total_files,
        "supported_files": job.supported_files,
        "total_loc": job.total_loc,
        "parse_success_count": job.parse_success_count,
        "parse_error_count": job.parse_error_count,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None
    }


@app.get("/api/jobs/{job_id}/chunks")
async def get_job_chunks(job_id: str) -> List[ParsedChunk]:
    """
    Get ParsedChunks for AI/ML team.
    
    This endpoint provides the LOCKED ParsedChunk contract data
    that AI/ML team needs for explanation/test generation.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or expired. Please start a new analysis."
        )
    
    if job.status not in ("done", "explaining", "testing", "refactoring"):
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready. Status: {job.status}"
        )
    
    if not job.analysis_data or "_analysis_obj" not in job.analysis_data:
        raise HTTPException(
            status_code=500,
            detail="Analysis data not available"
        )
    
    # Get the stored analysis object
    analysis = job.analysis_data["_analysis_obj"]

    # Convert to ParsedChunks using the fixed helper
    return _extract_chunks(analysis)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
