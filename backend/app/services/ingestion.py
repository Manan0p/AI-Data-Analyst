import hashlib
import io
import re
import pandas as pd
from fastapi import HTTPException, UploadFile
from app.config import settings
from app.database.registry import Dataset, DatasetRegistry


MAX_FILE_SIZE_BYTES = settings.max_upload_mb * 1024 * 1024
MAX_ROW_COUNT = settings.max_row_count


class CsvIngestionService:
    def __init__(self, registry: DatasetRegistry):
        self.registry = registry

    def ingest_bytes(self, filename: str, content: bytes, owner_id: str | None = None, dataset_id: str | None = None) -> Dataset:
        if not filename or not filename.lower().endswith(".csv"):
            raise HTTPException(400, "Only CSV files are supported")
        if not content.strip():
            raise HTTPException(400, f"{filename} is empty")
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(413, f"File size ({len(content)} bytes) exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB")

        decoded = None
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                decoded = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if decoded is None:
            decoded = content.decode("utf-8", errors="replace")

        try:
            frame = pd.read_csv(io.StringIO(decoded))
        except (pd.errors.ParserError, Exception) as exc:
            raise HTTPException(400, f"Malformed CSV: {exc}") from exc

        if frame.empty or not len(frame.columns):
            raise HTTPException(400, "CSV must contain headers and at least one data row")
        if len(frame) > MAX_ROW_COUNT:
            raise HTTPException(400, f"Dataset contains {len(frame)} rows, which exceeds maximum limit of {MAX_ROW_COUNT} rows")
        if frame.columns.duplicated().any():
            raise HTTPException(400, f"Duplicate column names: {frame.columns[frame.columns.duplicated()].tolist()}")

        # Auto-convert date columns to datetime objects for DuckDB SQL compatibility.
        # Only parse object columns with a high success ratio; numeric IDs such as
        # YEAR_ID and POSTAL_CODE must remain numeric measures/identifiers.
        for col in frame.columns:
            if frame[col].dtype == "object":
                if any(term in str(col).lower() for term in ("date", "time", "timestamp")):
                    try:
                        parsed = pd.to_datetime(frame[col], format="mixed", errors="coerce")
                        if len(parsed) and float(parsed.notna().mean()) >= 0.7:
                            frame[col] = parsed
                    except Exception:
                        pass

        # Owner-scoped full-content hash. This keeps serverless rehydration
        # deterministic while preventing identical uploads from different users
        # from overwriting one another.
        owner_scope = owner_id or "anonymous"
        seed = owner_scope.encode("utf-8") + b"\0" + filename.encode("utf-8") + b"\0" + content
        if dataset_id is not None and not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", dataset_id):
            raise HTTPException(400, "Invalid dataset identifier")
        dataset_id = dataset_id or ("ds_" + hashlib.sha256(seed).hexdigest()[:16])

        dataset = Dataset(dataset_id, filename, frame, owner_id=owner_id)
        self.registry.add(dataset, owner_id=owner_id)

        # Fire-and-forget: auto-analysis runs in background thread pool
        try:
            from app.analytics.auto_analysis import AutoAnalysisEngine
            from app.services.jobs import job_manager
            _frame = frame.copy()
            _did   = dataset_id
            _oid   = owner_id

            def _analysis_task():
                AutoAnalysisEngine().run_and_persist(_did, _frame, owner_id=_oid)

            job_id = job_manager.submit_job("auto_analysis", owner_id or "anon", _analysis_task)
            job = job_manager.get_job(job_id)
            if job is not None:
                setattr(job, "dataset_id", dataset_id)
        except Exception as exc:
            # Never block ingestion because of analysis errors
            import logging
            logging.getLogger(__name__).warning("Auto-analysis job submission failed: %s", exc)

        return dataset

    async def ingest(self, upload: UploadFile, owner_id: str | None = None, dataset_id: str | None = None) -> Dataset:
        content = await upload.read()
        return self.ingest_bytes(upload.filename or "upload.csv", content, owner_id=owner_id, dataset_id=dataset_id)
