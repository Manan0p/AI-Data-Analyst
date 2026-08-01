import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

import pandas as pd


@dataclass
class Dataset:
    id: str
    name: str
    frame: pd.DataFrame


class DatasetRegistry:
    def __init__(self):
        self._items: dict[str, Dataset] = {}
        self._lock = RLock()
        
        # Configure disk persistence directory
        # Try local data directory first, fallback to system temp directory if permission denied
        local_dir = Path(__file__).parent.parent.parent / "data" / "uploads"
        try:
            local_dir.mkdir(parents=True, exist_ok=True)
            self._storage_dir = local_dir
        except Exception:
            temp_dir = Path(tempfile.gettempdir()) / "ai_data_analyst_uploads"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self._storage_dir = temp_dir

    def _save_to_disk(self, dataset: Dataset) -> None:
        """Persist CSV frame and metadata JSON to disk."""
        try:
            csv_path = self._storage_dir / f"{dataset.id}.csv"
            meta_path = self._storage_dir / f"{dataset.id}.json"

            dataset.frame.to_csv(csv_path, index=False)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({"id": dataset.id, "name": dataset.name}, f)
        except Exception:
            pass

    def _load_from_disk(self, dataset_id: str) -> Dataset | None:
        """Restore a dataset from disk if present."""
        csv_path = self._storage_dir / f"{dataset_id}.csv"
        meta_path = self._storage_dir / f"{dataset_id}.json"

        if not (csv_path.exists() and meta_path.exists()):
            return None

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            frame = pd.read_csv(csv_path)
            dataset = Dataset(id=meta["id"], name=meta["name"], frame=frame)
            self._items[dataset.id] = dataset
            return dataset
        except Exception:
            return None

    def add(self, dataset: Dataset):
        with self._lock:
            self._items[dataset.id] = dataset
            self._save_to_disk(dataset)

    def get(self, dataset_id: str) -> Dataset:
        with self._lock:
            if dataset_id in self._items:
                return self._items[dataset_id]

            # Try loading from disk persistence
            restored = self._load_from_disk(dataset_id)
            if restored:
                return restored

            raise KeyError(f"Dataset '{dataset_id}' was not found")

    def list(self) -> list[Dataset]:
        with self._lock:
            # Sync with disk to recover any stored datasets
            if self._storage_dir.exists():
                for meta_file in self._storage_dir.glob("*.json"):
                    dataset_id = meta_file.stem
                    if dataset_id not in self._items:
                        self._load_from_disk(dataset_id)

            return list(self._items.values())

    def clear(self) -> None:
        """Clear memory and remove stored files (used for testing and resets)."""
        with self._lock:
            self._items.clear()
            if self._storage_dir.exists():
                for f in self._storage_dir.glob("*"):
                    try:
                        f.unlink()
                    except Exception:
                        pass

    @staticmethod
    def table_name(dataset_id: str) -> str:
        return "dataset_" + re.sub(r"[^a-zA-Z0-9_]", "_", dataset_id)


registry = DatasetRegistry()
