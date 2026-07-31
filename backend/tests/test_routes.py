import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_and_datasets_flow():
    csv_content = b"product,sales,quantity\nWidget A,150.5,10\nWidget B,200.0,5\n"
    response = client.post(
        "/api/upload",
        files=[("files", ("products.csv", io.BytesIO(csv_content), "text/csv"))]
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    dataset_id = data[0]["id"]
    assert data[0]["name"] == "products.csv"
    assert data[0]["rows"] == 2

    # Fetch datasets list
    ds_resp = client.get("/api/datasets")
    assert ds_resp.status_code == 200
    assert len(ds_resp.json()) >= 1

    # Get dataset rows
    rows_resp = client.get(f"/api/datasets/{dataset_id}/rows")
    assert rows_resp.status_code == 200
    assert rows_resp.json()["total"] == 2

    # Get profile
    profile_resp = client.get(f"/api/datasets/{dataset_id}/profile")
    assert profile_resp.status_code == 200
    assert profile_resp.json()["rows"] == 2

    # SQL endpoint
    sql_resp = client.post("/api/generate-sql", json={
        "dataset_id": dataset_id,
        "query": "SELECT product, sales FROM dataset_" + dataset_id.replace('-', '_') + " WHERE sales > 160"
    })
    assert sql_resp.status_code == 200
    assert len(sql_resp.json()["metadata"]["rows"]) == 1
