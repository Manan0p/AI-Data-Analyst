import io
import json
import logging
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.services.ingestion import CsvIngestionService
from app.database.registry import DatasetRegistry
from app.core.logging_config import setup_logging
from app.config import settings


client = TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    import uuid
    email = f"guardrails_{uuid.uuid4().hex[:8]}@example.com"
    password = "SafePassword123!"
    reg_resp = client.post("/api/auth/register", json={"email": email, "password": password})
    token = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_oversized_file_rejected_413(auth_headers: dict[str, str]):
    # Test that content exceeding MAX_FILE_SIZE_BYTES raises 413
    huge_size = 26 * 1024 * 1024  # 26 MB
    service = CsvIngestionService(DatasetRegistry())
    dummy_huge_content = b"a,b,c\n" + (b"0" * huge_size)

    with pytest.raises(HTTPException) as exc_info:
        service.ingest_bytes("huge.csv", dummy_huge_content)

    assert exc_info.value.status_code == 413
    assert "exceeds maximum limit" in exc_info.value.detail


def test_excessive_rows_rejected_400():
    # Test that row count exceeding MAX_ROW_COUNT raises 400
    service = CsvIngestionService(DatasetRegistry())
    
    # We monkeypatch settings.max_row_count to 10 for test speed
    with patch.object(settings, "max_row_count", 10):
        rows_csv = "col1,col2\n" + "\n".join([f"{i},{i*2}" for i in range(15)])
        
        # Also need to patch MAX_ROW_COUNT in ingestion module if imported directly
        with patch("app.services.ingestion.MAX_ROW_COUNT", 10):
            with pytest.raises(HTTPException) as exc_info:
                service.ingest_bytes("too_many_rows.csv", rows_csv.encode("utf-8"))

            assert exc_info.value.status_code == 400
            assert "exceeds maximum limit of 10 rows" in exc_info.value.detail


def test_rate_limiting_enforced_on_upload(auth_headers: dict[str, str]):
    # Upload limit is 10/minute. Firing 12 requests quickly should trigger HTTP 429.
    triggered_429 = False
    for i in range(15):
        csv_data = f"id,val\n{i},100\n".encode("utf-8")
        resp = client.post(
            "/api/upload",
            files={"files": (f"rate_test_{i}.csv", io.BytesIO(csv_data), "text/csv")},
            headers=auth_headers,
        )
        if resp.status_code == 429:
            triggered_429 = True
            assert "Rate limit exceeded" in resp.text
            break

    assert triggered_429, "Rate limiter did not trigger 429 status code"


def test_structured_json_logging_output(monkeypatch):
    # Verify setup_logging emits JSON formatted log lines
    monkeypatch.setattr(settings, "log_format", "json")
    setup_logging()

    logger = logging.getLogger("test_structured_logger")
    log_stream = io.StringIO()
    handler = logger.root.handlers[0]
    
    # Replace stdout stream temporarily to inspect output
    old_stream = handler.stream
    handler.stream = log_stream
    try:
        logger.info("Test structured observability message")
        output = log_stream.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["message"] == "Test structured observability message"
        assert parsed["levelname"] == "INFO"
        assert "asctime" in parsed
    finally:
        handler.stream = old_stream
