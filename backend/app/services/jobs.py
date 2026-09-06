from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
from threading import RLock
from typing import Any, Callable, Optional
import uuid

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    user_id: Optional[str]
    job_type: str
    status: JobStatus = JobStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class JobManager:
    def __init__(self, max_workers: int = 4):
        self._jobs: dict[str, Job] = {}
        self._lock = RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="insightforge-worker")

    def submit_job(
        self,
        job_type: str,
        user_id: Optional[str],
        fn: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = Job(id=job_id, user_id=user_id, job_type=job_type, status=JobStatus.PROCESSING)

        with self._lock:
            self._jobs[job_id] = job

        def _worker():
            try:
                logger.info("Starting background job %s (type: %s)", job_id, job_type)
                res = fn(*args, **kwargs)
                with self._lock:
                    job.status = JobStatus.COMPLETED
                    job.result = res
                logger.info("Background job %s completed successfully", job_id)
            except Exception as exc:
                logger.error("Background job %s failed: %s", job_id, exc, exc_info=True)
                with self._lock:
                    job.status = JobStatus.FAILED
                    job.error = str(exc)

        self._executor.submit(_worker)
        return job_id

    def get_job(self, job_id: str, user_id: Optional[str] = None) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            if user_id is not None and job.user_id is not None and job.user_id != user_id:
                return None
            return job


job_manager = JobManager()
