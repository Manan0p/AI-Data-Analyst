import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_user_success():
    email = f"analyst_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "securepassword123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email


def test_register_duplicate_email_rejected():
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    res1 = client.post("/api/auth/register", json={
        "email": email,
        "password": "password123"
    })
    assert res1.status_code == 200
    res2 = client.post("/api/auth/register", json={
        "email": email,
        "password": "password123"
    })
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_login_success():
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "mysecretpassword"
    })
    res = client.post("/api/auth/login", json={
        "email": email,
        "password": "mysecretpassword"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password():
    email = f"wrongpwd_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "correctpassword"
    })
    res = client.post("/api/auth/login", json={
        "email": email,
        "password": "incorrectpassword"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_login_nonexistent_user():
    res = client.post("/api/auth/login", json={
        "email": f"ghost_{uuid.uuid4().hex[:8]}@example.com",
        "password": "nopassword"
    })
    assert res.status_code == 401


def test_unauthenticated_request_rejected():
    res = client.get("/api/datasets")
    assert res.status_code == 401


def test_invalid_token_rejected():
    headers = {"Authorization": "Bearer not-a-valid-token-string"}
    res = client.get("/api/datasets", headers=headers)
    assert res.status_code == 401


def test_per_user_dataset_isolation():
    # 1. Register User A
    alice_email = f"alice_{uuid.uuid4().hex[:8]}@company.com"
    u1_res = client.post("/api/auth/register", json={
        "email": alice_email,
        "password": "passwordAlice1"
    })
    assert u1_res.status_code == 200
    u1_reg = u1_res.json()
    u1_headers = {"Authorization": f"Bearer {u1_reg['access_token']}"}

    # 2. Register User B
    bob_email = f"bob_{uuid.uuid4().hex[:8]}@company.com"
    u2_res = client.post("/api/auth/register", json={
        "email": bob_email,
        "password": "passwordBob1"
    })
    assert u2_res.status_code == 200
    u2_reg = u2_res.json()
    u2_headers = {"Authorization": f"Bearer {u2_reg['access_token']}"}

    # 3. User A uploads Dataset A
    csv_a = b"dept,salary\nengineering,120\nengineering,140\n"
    res_a = client.post(
        "/api/upload",
        files=[("files", ("alice_data.csv", io.BytesIO(csv_a), "text/csv"))],
        headers=u1_headers
    )
    assert res_a.status_code == 200
    dataset_a_id = res_a.json()[0]["id"]

    # 4. User B uploads Dataset B
    csv_b = b"customer,revenue\nAcme,500\nGlobex,900\n"
    res_b = client.post(
        "/api/upload",
        files=[("files", ("bob_data.csv", io.BytesIO(csv_b), "text/csv"))],
        headers=u2_headers
    )
    assert res_b.status_code == 200
    dataset_b_id = res_b.json()[0]["id"]

    # 5. User A lists datasets — sees only Dataset A
    u1_list = client.get("/api/datasets", headers=u1_headers).json()
    u1_ids = [d["id"] for d in u1_list]
    assert dataset_a_id in u1_ids
    assert dataset_b_id not in u1_ids

    # 6. User B lists datasets — sees only Dataset B
    u2_list = client.get("/api/datasets", headers=u2_headers).json()
    u2_ids = [d["id"] for d in u2_list]
    assert dataset_b_id in u2_ids
    assert dataset_a_id not in u2_ids

    # 7. User B attempts to access User A's dataset rows — rejected with 404
    u2_access_a = client.get(f"/api/datasets/{dataset_a_id}/rows", headers=u2_headers)
    assert u2_access_a.status_code == 404

    # 8. User B attempts to delete User A's dataset — rejected with 404
    u2_del_a = client.delete(f"/api/datasets/{dataset_a_id}", headers=u2_headers)
    assert u2_del_a.status_code == 404

    # 9. User A clears their datasets — only User A's dataset is deleted, User B's remains intact
    u1_clear = client.delete("/api/datasets", headers=u1_headers)
    assert u1_clear.status_code == 200
    assert len(client.get("/api/datasets", headers=u1_headers).json()) == 0

    u2_recheck = client.get("/api/datasets", headers=u2_headers).json()
    assert any(d["id"] == dataset_b_id for d in u2_recheck)

