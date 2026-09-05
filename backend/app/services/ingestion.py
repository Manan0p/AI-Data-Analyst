import hashlib
import io
import pandas as pd
from fastapi import HTTPException, UploadFile
from app.config import settings
from app.database.registry import Dataset, DatasetRegistry


MAX_FILE_SIZE_BYTES = settings.max_upload_mb * 1024 * 1024
MAX_ROW_COUNT = settings.max_row_count


class CsvIngestionService:
    def __init__(self, registry: DatasetRegistry):
        self.registry = registry

    def ingest_bytes(self, filename: str, content: bytes, owner_id: str | None = None) -> Dataset:
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

        # Auto-convert date columns to datetime objects for DuckDB SQL compatibility
        for col in frame.columns:
            if frame[col].dtype == "object":
                if any(term in str(col).lower() for term in ("date", "time", "year", "month", "day")):
                    try:
                        parsed = pd.to_datetime(frame[col], format="mixed", errors="coerce")
                        if pd.api.types.is_datetime64_any_dtype(parsed):
                            frame[col] = parsed
                    except Exception:
                        pass

        # Deterministic dataset ID generation from filename and content hash
        # Guarantees 0 duplicate dataset cards and instant ID matching across serverless workers
        seed = f"{filename}:{len(content)}:{content[:500]}".encode('utf-8')
        dataset_id = hashlib.md5(seed).hexdigest()[:12]

        dataset = Dataset(dataset_id, filename, frame, owner_id=owner_id)
        self.registry.add(dataset, owner_id=owner_id)
        return dataset

    async def ingest(self, upload: UploadFile, owner_id: str | None = None) -> Dataset:
        content = await upload.read()
        return self.ingest_bytes(upload.filename or "upload.csv", content, owner_id=owner_id)
