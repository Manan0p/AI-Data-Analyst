import uuid
from pathlib import Path
import pandas as pd
import pytest
from app.database.registry import Dataset, registry
from app.memory.session import ConversationMemory, memory


def test_dataset_persists_and_rehydrates_after_cache_clear():
    dataset_id = f"ds_{uuid.uuid4().hex[:8]}"
    df = pd.DataFrame({"category": ["A", "B", "C"], "val": [10, 20, 30]})
    ds = Dataset(id=dataset_id, name="test_persist.csv", frame=df, owner_id="user_test_1")

    registry.add(ds, owner_id="user_test_1")

    # Verify CSV file is created on storage
    csv_file = registry.upload_dir / f"{dataset_id}.csv"
    assert csv_file.exists()

    # Clear the in-memory RAM cache completely to simulate server restart / process recreation
    registry._cache.clear()
    assert dataset_id not in registry._cache

    # Re-fetch dataset — it must re-hydrate from DB metadata and storage file
    rehydrated = registry.get(dataset_id, owner_id="user_test_1")
    assert rehydrated.id == dataset_id
    assert rehydrated.name == "test_persist.csv"
    assert len(rehydrated.frame) == 3
    assert list(rehydrated.frame["category"]) == ["A", "B", "C"]

    # Clean up
    registry.delete(dataset_id, owner_id="user_test_1")


def test_chat_memory_persists_across_instances():
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    memory.add(session_id, "user", "What is the average sales?")
    memory.add(session_id, "assistant", "The average sales is $250.00.")

    # Wipe in-memory RAM cache
    memory._cache.clear()
    assert session_id not in memory._cache

    # Instantiate a new ConversationMemory instance to simulate server restart
    new_memory = ConversationMemory()
    history = new_memory.get(session_id)

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "What is the average sales?"}
    assert history[1] == {"role": "assistant", "content": "The average sales is $250.00."}

    # Clean up
    new_memory.clear(session_id)
    assert len(new_memory.get(session_id)) == 0


def test_dataset_deletion_removes_db_and_storage_file():
    dataset_id = f"ds_del_{uuid.uuid4().hex[:8]}"
    df = pd.DataFrame({"x": [1, 2]})
    ds = Dataset(id=dataset_id, name="delete_me.csv", frame=df, owner_id="user_del")

    registry.add(ds, owner_id="user_del")
    csv_file = registry.upload_dir / f"{dataset_id}.csv"
    assert csv_file.exists()

    # Delete dataset
    deleted = registry.delete(dataset_id, owner_id="user_del")
    assert deleted is True

    # Storage file must be deleted from disk
    assert not csv_file.exists()

    # Must no longer be retrievable
    with pytest.raises(KeyError):
        registry.get(dataset_id, owner_id="user_del")
