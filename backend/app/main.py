"""
CodeOracle Backend - Main FastAPI application.
Owned by Backend Engineer.
"""
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import tempfile
import asyncio
from typing import List, Dict

from .models.contract import JobStatus, ParsedChunk
from .jobs.job_manager import job_manager
from .ingestion.zip_handler import (
    extract_zip, create_workspace, cleanup_workspace,
    ZipValidationError, ZipSecurityError
)
from .parsing.repository_analyzer import RepositoryAnalyzer
from .parsing.contract_adapter import ParsedChunkAdapter
from .models.repository import Language

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


async def process_repository_job(job_id: str, zip_path: Path):
    """
    Background task to process repository.
    This runs the full analysis pipeline with timeout protection.
    """
    try:
        # Update status to parsing
        job_manager.update_status(job_id, "parsing", progress=10)
        
        # Create workspace
        workspace_dir, original_dir, working_dir, generated_tests_dir = create_workspace(
            job_id, TEMP_WORKSPACE_ROOT
        )
        job_manager.set_workspace(
            job_id, workspace_dir, original_dir, working_dir, generated_tests_dir
        )
        
        # Extract ZIP with timeout protection
        try:
            # Use asyncio timeout for the entire stage
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
        
        # Analyze repository with timeout protection
        try:
            async with asyncio.timeout(STAGE_TIMEOUT_SECONDS):
                analysis = await asyncio.to_thread(
                    repository_analyzer.analyze,
                    original_dir,
                    f"repo_{job_id}"
                )
            
            # Check LOC limit
            if analysis.total_loc > MAX_LOC:
                error_msg = f"Repository too large: {analysis.total_loc} LOC > {MAX_LOC} LOC"
                job_manager.set_error(job_id, "parse", error_msg)
                job_manager.update_status(job_id, "error", progress=0, error=error_msg)
                return
            
            # Store repository info
            job_manager.set_repository_info(
                job_id,
                analysis.repository_id,
                analysis.name,
                len(analysis.files),
                len(analysis.supported_files),
                analysis.total_loc
            )
            
            # Store parse results
            success_count = len(analysis.supported_files) - len(analysis.parse_errors)
            job_manager.set_parse_results(
                job_id,
                success_count,
                len(analysis.parse_errors)
            )
            
            # Store analysis data for later retrieval
            analysis_dict = {
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
                # Store the actual analysis object for ParsedChunk generation
                "_analysis_obj": analysis
            }
            job_manager.set_analysis_data(job_id, analysis_dict)
            
            job_manager.update_status(job_id, "parsing", progress=70)
            
            # TODO: Here AI/ML and API/Integration teams will add their stages:
            # - explaining (AI/ML)
            # - testing (AI/ML + Backend)
            # - refactoring (AI/ML)
            
            # For now, mark as done after parsing
            job_manager.update_status(job_id, "done", progress=100)
            
        except asyncio.TimeoutError:
            error_msg = f"Repository analysis timeout after {STAGE_TIMEOUT_SECONDS}s"
            job_manager.set_error(job_id, "parse", error_msg)
            job_manager.update_status(job_id, "error", progress=0, error=error_msg)
            return
        except Exception as e:
            job_manager.set_error(job_id, "parse", str(e))
            job_manager.update_status(job_id, "error", progress=0, error=f"Parse error: {e}")
            return
    
    except Exception as e:
        job_manager.update_status(job_id, "error", progress=0, error=f"Job failed: {e}")
    
    finally:
        # Cleanup uploaded ZIP
        if zip_path.exists():
            try:
                zip_path.unlink()
            except:
                pass


@app.post("/api/upload")
async def upload_repository(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a repository ZIP file for analysis.
    
    This endpoint is part of the LOCKED contract (CONTRACT.md §2).
    """
    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are supported"
        )
    
    # Create job
    job_id = job_manager.create_job()
    
    # Save uploaded file temporarily
    temp_zip = TEMP_WORKSPACE_ROOT / f"upload_{job_id}.zip"
    
    try:
        with open(temp_zip, 'wb') as f:
            content = await file.read()
            
            # Check size
            size_mb = len(content) / (1024 * 1024)
            if size_mb > MAX_UPLOAD_SIZE_MB:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large: {size_mb:.1f}MB > {MAX_UPLOAD_SIZE_MB}MB"
                )
            
            f.write(content)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    
    # Start background processing
    background_tasks.add_task(process_repository_job, job_id, temp_zip)
    
    # Return job ID per CONTRACT.md
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
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Return LOCKED contract status
    return JobStatus(
        status=job.status,
        progress=job.progress,
        error=job.error
    )


@app.get("/api/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """
    Get job result.
    
    This endpoint is part of the LOCKED contract (CONTRACT.md §2).
    Currently returns basic parsing results.
    AI/ML and API/Integration teams will enhance this.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Job not done yet. Status: {job.status}"
        )
    
    # For now, return empty structures matching CONTRACT.md
    # Other teams will populate these
    return {
        "explanation": {
            "modules": [],
            "functions": []
        },
        "dependency_graph": {
            "nodes": [],
            "edges": []
        },
        "tests": {
            "test_files": [],
            "coverage_percent": 0.0,
            "passed": 0,
            "failed": 0,
            "log": ""
        },
        "refactor": {
            "files": []
        }
    }


@app.get("/api/jobs/{job_id}/analysis")
async def get_job_analysis(job_id: str):
    """
    Get internal repository analysis details.
    This is a backend-internal endpoint for debugging/integration.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
        raise HTTPException(status_code=404, detail="Job not found")
    
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
    
    # Convert to ParsedChunks
    chunks: List[ParsedChunk] = []
    
    # Group by language and convert
    for lang in analysis.languages:
        lang_functions = [
            f for f in analysis.functions.values()
            if Path(f.file).suffix in {'.py': Language.PYTHON, '.js': Language.JAVASCRIPT, '.jsx': Language.JAVASCRIPT}.get(Path(f.file).suffix, None) == lang
        ]
        lang_classes = [
            c for c in analysis.classes.values()
            if Path(c.file).suffix in {'.py': Language.PYTHON, '.js': Language.JAVASCRIPT, '.jsx': Language.JAVASCRIPT}.get(Path(c.file).suffix, None) == lang
        ]
        
        chunks.extend(
            ParsedChunkAdapter.from_repository_analysis(
                lang_functions, lang_classes, lang
            )
        )
    
    return chunks


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
