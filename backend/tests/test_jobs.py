import io
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    unique_email = f"jobuser_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": unique_email,
        "password": "jobuserpassword123"
    })
    res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "jobuserpassword123"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_async_upload_and_polling_flow(auth_headers):
    csv_bytes = b"feature_a,feature_b\n10,20\n30,40\n50,60\n"
    # 1. Post async upload
    upload_res = client.post(
        "/api/upload/async",
        files=[("files", ("async_data.csv", io.BytesIO(csv_bytes), "text/csv"))],
        headers=auth_headers
    )
    assert upload_res.status_code == 202
    job_info = upload_res.json()
    assert "job_id" in job_info
    assert job_info["job_type"] == "csv_ingestion"
    assert job_info["status"] in ("processing", "pending", "completed")

    job_id = job_info["job_id"]

    # 2. Poll job status until completed
    max_wait_seconds = 5
    start_time = time.time()
    completed = False
    result_payload = None

    while time.time() - start_time < max_wait_seconds:
        poll_res = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        if poll_data["status"] == "completed":
            completed = True
            result_payload = poll_data["result"]
            break
        time.sleep(0.1)

    assert completed is True
    assert result_payload is not None
    assert len(result_payload) == 1
    assert result_payload[0]["name"] == "async_data.csv"
    assert result_payload[0]["rows"] == 3


def test_async_anomaly_detection_flow(auth_headers):
    # 1. Upload sample dataset
    csv_bytes = b"val1,val2\n1.0,2.0\n1.1,2.1\n0.9,1.9\n100.0,500.0\n"
    upload_res = client.post(
        "/api/upload",
        files=[("files", ("anomaly_test.csv", io.BytesIO(csv_bytes), "text/csv"))],
        headers=auth_headers
    )
    assert upload_res.status_code == 200
    dataset_id = upload_res.json()[0]["id"]

    # 2. Submit async anomaly detection
    anomaly_res = client.post(
        f"/api/detect-anomalies/async?dataset_id={dataset_id}",
        headers=auth_headers
    )
    assert anomaly_res.status_code == 202
    job_id = anomaly_res.json()["job_id"]

    # 3. Poll for completion
    start = time.time()
    completed = False
    result = None
    while time.time() - start < 5:
        p = client.get(f"/api/jobs/{job_id}", headers=auth_headers).json()
        if p["status"] == "completed":
            completed = True
            result = p["result"]
            break
        time.sleep(0.1)

    assert completed is True
    assert isinstance(result, list)


def test_job_access_isolation(auth_headers):
    # 1. User A starts an async job
    csv_bytes = b"x,y\n1,2\n"
    res_a = client.post(
        "/api/upload/async",
        files=[("files", ("secret.csv", io.BytesIO(csv_bytes), "text/csv"))],
        headers=auth_headers
    )
    job_id = res_a.json()["job_id"]

    # 2. Register User B
    b_email = f"user_b_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={"email": b_email, "password": "passwordB123"})
    token_b = client.post("/api/auth/login", json={"email": b_email, "password": "passwordB123"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B tries to poll User A's job -> 404
    poll_b = client.get(f"/api/jobs/{job_id}", headers=headers_b)
    assert poll_b.status_code == 404


def test_nonexistent_job_returns_404(auth_headers):
    res = client.get("/api/jobs/nonexistent_job_id_123", headers=auth_headers)
    assert res.status_code == 404
