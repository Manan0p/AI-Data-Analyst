import hashlib
import io
import pandas as pd
from fastapi import HTTPException, UploadFile
from app.database.registry import Dataset, DatasetRegistry


class CsvIngestionService:
    def __init__(self, registry: DatasetRegistry):
        self.registry = registry

    async def ingest(self, upload: UploadFile) -> Dataset:
        if not upload.filename or not upload.filename.lower().endswith(".csv"):
            raise HTTPException(400, "Only CSV files are supported")
        content = await upload.read()
        if not content.strip():
            raise HTTPException(400, f"{upload.filename} is empty")

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
        if frame.columns.duplicated().any():
            raise HTTPException(400, f"Duplicate column names: {frame.columns[frame.columns.duplicated()].tolist()}")

        # Auto-convert date columns to datetime objects for DuckDB SQL compatibility
        for col in frame.columns:
            if frame[col].dtype == "object":
                if any(term in str(col).lower() for term in ("date", "time", "year", "month", "day")):
                    try:
                        parsed = pd.to_datetime(frame[col], format="mixed", errors="ignore")
                        if pd.api.types.is_datetime64_any_dtype(parsed):
                            frame[col] = parsed
                    except Exception:
                        pass

        # Generate a deterministic dataset ID from filename and content hash
        # Ensures re-uploading/re-hydrating the same CSV produces the exact same dataset ID
        seed = f"{upload.filename}:{len(content)}:{content[:500]}".encode('utf-8')
        dataset_id = hashlib.md5(seed).hexdigest()[:12]

        dataset = Dataset(dataset_id, upload.filename, frame)
        self.registry.add(dataset)
        return dataset
