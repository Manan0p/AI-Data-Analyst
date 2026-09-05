import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

import pandas as pd
from app.config import settings
from app.database.connection import SessionLocal
from app.database.models import DatasetModel

logger = logging.getLogger(__name__)


@dataclass
class Dataset:
    id: str
    name: str
    frame: pd.DataFrame
    owner_id: str | None = None


class DatasetRegistry:
    def __init__(self):
        self._cache: dict[str, Dataset] = {}
        self._lock = RLock()
        self.upload_dir: Path = settings.upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def add(self, dataset: Dataset, owner_id: str | None = None):
        with self._lock:
            effective_owner = owner_id or dataset.owner_id
            dataset.owner_id = effective_owner
            self._cache[dataset.id] = dataset

            # 1. Persist CSV payload to storage volume
            csv_path = self.upload_dir / f"{dataset.id}.csv"
            dataset.frame.to_csv(csv_path, index=False)
            storage_key = str(csv_path)

            # 2. Persist metadata to database
            db = SessionLocal()
            try:
                schema_dict = {str(col): str(dataset.frame[col].dtype) for col in dataset.frame.columns}
                existing = db.query(DatasetModel).filter(DatasetModel.id == dataset.id).first()
                if existing:
                    existing.owner_id = effective_owner
                    existing.filename = dataset.name
                    existing.storage_key = storage_key
                    existing.row_count = len(dataset.frame)
                    existing.column_schema = schema_dict
                else:
                    rec = DatasetModel(
                        id=dataset.id,
                        owner_id=effective_owner,
                        filename=dataset.name,
                        storage_key=storage_key,
                        row_count=len(dataset.frame),
                        column_schema=schema_dict,
                    )
                    db.add(rec)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("Failed to persist dataset metadata to database: %s", exc)
            finally:
                db.close()

    def get(self, dataset_id: str, owner_id: str | None = None) -> Dataset:
        with self._lock:
            # 1. Check in-memory fast cache
            if dataset_id in self._cache:
                item = self._cache[dataset_id]
                if owner_id is not None and item.owner_id is not None and item.owner_id != owner_id:
                    raise KeyError(f"Dataset '{dataset_id}' was not found")
                return item

            # 2. Rehydrate from DB and file storage
            db = SessionLocal()
            try:
                query = db.query(DatasetModel).filter(DatasetModel.id == dataset_id)
                if owner_id is not None:
                    query = query.filter((DatasetModel.owner_id == owner_id) | (DatasetModel.owner_id.is_(None)))
                rec = query.first()
                if not rec:
                    raise KeyError(f"Dataset '{dataset_id}' was not found")

                storage_path = Path(rec.storage_key)
                if not storage_path.exists():
                    raise KeyError(f"Dataset file for '{dataset_id}' not found on storage")

                frame = pd.read_csv(storage_path)
                item = Dataset(id=rec.id, name=rec.filename, frame=frame, owner_id=rec.owner_id)
                self._cache[rec.id] = item
                return item
            finally:
                db.close()

    def delete(self, dataset_id: str, owner_id: str | None = None) -> bool:
        with self._lock:
            db = SessionLocal()
            found = False
            try:
                query = db.query(DatasetModel).filter(DatasetModel.id == dataset_id)
                if owner_id is not None:
                    query = query.filter((DatasetModel.owner_id == owner_id) | (DatasetModel.owner_id.is_(None)))
                rec = query.first()
                if rec:
                    found = True
                    storage_path = Path(rec.storage_key)
                    if storage_path.exists():
                        try:
                            storage_path.unlink()
                        except Exception:
                            pass
                    db.delete(rec)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("Error deleting dataset from DB: %s", exc)
            finally:
                db.close()

            if dataset_id in self._cache:
                item = self._cache[dataset_id]
                if owner_id is not None and item.owner_id is not None and item.owner_id != owner_id:
                    return False
                del self._cache[dataset_id]
                found = True

            return found

    def list(self, owner_id: str | None = None) -> list[Dataset]:
        with self._lock:
            db = SessionLocal()
            datasets: list[Dataset] = []
            try:
                query = db.query(DatasetModel)
                if owner_id is not None:
                    query = query.filter((DatasetModel.owner_id == owner_id) | (DatasetModel.owner_id.is_(None)))
                records = query.all()
                for rec in records:
                    if rec.id in self._cache:
                        datasets.append(self._cache[rec.id])
                    else:
                        storage_path = Path(rec.storage_key)
                        if storage_path.exists():
                            frame = pd.read_csv(storage_path)
                            ds = Dataset(id=rec.id, name=rec.filename, frame=frame, owner_id=rec.owner_id)
                            self._cache[rec.id] = ds
                            datasets.append(ds)
                return datasets
            except Exception as exc:
                logger.warning("Failed to list datasets from DB; falling back to cache: %s", exc)
                if owner_id is not None:
                    return [d for d in self._cache.values() if d.owner_id is None or d.owner_id == owner_id]
                return list(self._cache.values())
            finally:
                db.close()

    def clear(self, owner_id: str | None = None) -> None:
        """Clear datasets for owner or entire registry."""
        with self._lock:
            db = SessionLocal()
            try:
                query = db.query(DatasetModel)
                if owner_id is not None:
                    query = query.filter(DatasetModel.owner_id == owner_id)
                recs = query.all()
                for rec in recs:
                    storage_path = Path(rec.storage_key)
                    if storage_path.exists():
                        try:
                            storage_path.unlink()
                        except Exception:
                            pass
                    db.delete(rec)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("Failed to clear datasets from DB: %s", exc)
            finally:
                db.close()

            if owner_id is not None:
                to_delete = [k for k, v in self._cache.items() if v.owner_id == owner_id]
                for k in to_delete:
                    del self._cache[k]
            else:
                self._cache.clear()

    @staticmethod
    def table_name(dataset_id: str) -> str:
        return "dataset_" + re.sub(r"[^a-zA-Z0-9_]", "_", dataset_id)


registry = DatasetRegistry()
