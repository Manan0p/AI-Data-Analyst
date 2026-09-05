import re
from dataclasses import dataclass
from threading import RLock

import pandas as pd


@dataclass
class Dataset:
    id: str
    name: str
    frame: pd.DataFrame
    owner_id: str | None = None


class DatasetRegistry:
    def __init__(self):
        self._items: dict[str, Dataset] = {}
        self._lock = RLock()

    def add(self, dataset: Dataset, owner_id: str | None = None):
        with self._lock:
            if owner_id is not None:
                dataset.owner_id = owner_id
            self._items[dataset.id] = dataset

    def get(self, dataset_id: str, owner_id: str | None = None) -> Dataset:
        with self._lock:
            if dataset_id not in self._items:
                raise KeyError(f"Dataset '{dataset_id}' was not found")
            item = self._items[dataset_id]
            if owner_id is not None and item.owner_id is not None and item.owner_id != owner_id:
                raise KeyError(f"Dataset '{dataset_id}' was not found")
            return item

    def delete(self, dataset_id: str, owner_id: str | None = None) -> bool:
        with self._lock:
            if dataset_id in self._items:
                item = self._items[dataset_id]
                if owner_id is not None and item.owner_id is not None and item.owner_id != owner_id:
                    return False
                del self._items[dataset_id]
                return True
            return False

    def list(self, owner_id: str | None = None) -> list[Dataset]:
        with self._lock:
            if owner_id is not None:
                return [d for d in self._items.values() if d.owner_id == owner_id]
            return list(self._items.values())

    def clear(self, owner_id: str | None = None) -> None:
        """Clear memory."""
        with self._lock:
            if owner_id is not None:
                to_delete = [k for k, v in self._items.items() if v.owner_id == owner_id]
                for k in to_delete:
                    del self._items[k]
            else:
                self._items.clear()

    @staticmethod
    def table_name(dataset_id: str) -> str:
        return "dataset_" + re.sub(r"[^a-zA-Z0-9_]", "_", dataset_id)


registry = DatasetRegistry()
