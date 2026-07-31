import re
from dataclasses import dataclass
from threading import RLock
import pandas as pd
@dataclass
class Dataset: id: str; name: str; frame: pd.DataFrame
class DatasetRegistry:
    def __init__(self): self._items: dict[str, Dataset] = {}; self._lock = RLock()
    def add(self, dataset: Dataset):
        with self._lock: self._items[dataset.id] = dataset
    def get(self, dataset_id: str) -> Dataset:
        with self._lock:
            if dataset_id not in self._items: raise KeyError(f"Dataset '{dataset_id}' was not found")
            return self._items[dataset_id]
    def list(self) -> list[Dataset]:
        with self._lock: return list(self._items.values())
    @staticmethod
    def table_name(dataset_id: str) -> str: return "dataset_" + re.sub(r"[^a-zA-Z0-9_]", "_", dataset_id)
registry = DatasetRegistry()
