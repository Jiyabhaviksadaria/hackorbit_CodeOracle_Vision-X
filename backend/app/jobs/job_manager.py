"""Job state management."""
import uuid
from datetime import datetime
from typing import Dict, Optional, Literal
from dataclasses import dataclass, field
from pathlib import Path


JobStatusType = Literal["queued", "parsing", "explaining", "testing", "refactoring", "done", "error"]


@dataclass
class JobState:
    """
    Internal job state - richer than public status.
    Public statuses remain LOCKED per CONTRACT.md.
    """
    job_id: str
    status: JobStatusType
    progress: int = 0
    error: Optional[str] = None
    
    # Internal fields (not exposed in public status)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    # Workspace paths
    workspace_dir: Optional[Path] = None
    original_dir: Optional[Path] = None
    working_dir: Optional[Path] = None
    generated_tests_dir: Optional[Path] = None
    
    # Repository info
    repository_name: Optional[str] = None
    total_files: int = 0
    supported_files: int = 0
    total_loc: int = 0
    
    # Stage results
    repository_id: Optional[str] = None
    parse_success_count: int = 0
    parse_error_count: int = 0
    
    # Store the actual analysis for retrieval
    analysis_data: Optional[Dict] = None
    
    # Errors by stage
    ingestion_error: Optional[str] = None
    parse_error: Optional[str] = None
    ai_error: Optional[str] = None
    test_error: Optional[str] = None


class JobManager:
    """
    Simple in-memory job manager.
    For MVP, we don't need a database.
    """
    
    def __init__(self):
        """Initialize job manager."""
        self.jobs: Dict[str, JobState] = {}
    
    def create_job(self) -> str:
        """
        Create a new job.
        
        Returns:
            job_id
        """
        job_id = str(uuid.uuid4())
        
        job = JobState(
            job_id=job_id,
            status="queued",
            progress=0
        )
        
        self.jobs[job_id] = job
        return job_id
    
    def get_job(self, job_id: str) -> Optional[JobState]:
        """Get job state."""
        return self.jobs.get(job_id)
    
    def update_status(
        self,
        job_id: str,
        status: JobStatusType,
        progress: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Update job status."""
        job = self.jobs.get(job_id)
        if not job:
            return
        
        job.status = status
        
        if progress is not None:
            job.progress = progress
        
        if error:
            job.error = error
        
        if status == "parsing" and not job.started_at:
            job.started_at = datetime.now()
        
        if status in ("done", "error"):
            job.finished_at = datetime.now()
    
    def set_workspace(
        self,
        job_id: str,
        workspace_dir: Path,
        original_dir: Path,
        working_dir: Path,
        generated_tests_dir: Path
    ):
        """Set workspace paths for job."""
        job = self.jobs.get(job_id)
        if job:
            job.workspace_dir = workspace_dir
            job.original_dir = original_dir
            job.working_dir = working_dir
            job.generated_tests_dir = generated_tests_dir
    
    def set_repository_info(
        self,
        job_id: str,
        repository_id: str,
        repository_name: str,
        total_files: int,
        supported_files: int,
        total_loc: int
    ):
        """Set repository information."""
        job = self.jobs.get(job_id)
        if job:
            job.repository_id = repository_id
            job.repository_name = repository_name
            job.total_files = total_files
            job.supported_files = supported_files
            job.total_loc = total_loc
    
    def set_parse_results(
        self,
        job_id: str,
        success_count: int,
        error_count: int
    ):
        """Set parse results."""
        job = self.jobs.get(job_id)
        if job:
            job.parse_success_count = success_count
            job.parse_error_count = error_count
    
    def set_error(
        self,
        job_id: str,
        stage: Literal["ingestion", "parse", "ai", "test"],
        error: str
    ):
        """Set error for a specific stage."""
        job = self.jobs.get(job_id)
        if job:
            if stage == "ingestion":
                job.ingestion_error = error
            elif stage == "parse":
                job.parse_error = error
            elif stage == "ai":
                job.ai_error = error
            elif stage == "test":
                job.test_error = error
    
    def set_analysis_data(self, job_id: str, analysis_data: Dict):
        """Store analysis data for later retrieval."""
        job = self.jobs.get(job_id)
        if job:
            job.analysis_data = analysis_data


# Global job manager instance
job_manager = JobManager()
