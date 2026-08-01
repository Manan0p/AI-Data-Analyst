import io
import asyncio
import pytest
from fastapi import UploadFile, HTTPException
from app.database.registry import DatasetRegistry
from app.services.ingestion import CsvIngestionService

def test_csv_ingestion_success():
    registry = DatasetRegistry()
    registry.clear()
    service = CsvIngestionService(registry)
    
    content = b"region,sales,quantity\nNorth,100,5\nSouth,200,10\n"
    upload_file = UploadFile(filename="test_sales.csv", file=io.BytesIO(content))
    
    dataset = asyncio.run(service.ingest(upload_file))
    assert dataset.name == "test_sales.csv"
    assert len(dataset.frame) == 2
    assert list(dataset.frame.columns) == ["region", "sales", "quantity"]
    assert len(registry.list()) == 1

def test_csv_ingestion_non_csv():
    registry = DatasetRegistry()
    registry.clear()
    service = CsvIngestionService(registry)
    
    upload_file = UploadFile(filename="test.txt", file=io.BytesIO(b"hello world"))
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.ingest(upload_file))
    assert exc_info.value.status_code == 400
    assert "Only CSV files are supported" in str(exc_info.value.detail)

def test_csv_ingestion_empty_file():
    registry = DatasetRegistry()
    registry.clear()
    service = CsvIngestionService(registry)
    
    upload_file = UploadFile(filename="empty.csv", file=io.BytesIO(b""))
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.ingest(upload_file))
    assert exc_info.value.status_code == 400
    assert "is empty" in str(exc_info.value.detail)
