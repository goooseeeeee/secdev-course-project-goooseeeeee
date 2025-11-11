import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body and body["error"]["code"] == "not_found"


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"


def test_large_file_rejected():
    file_content = b"X" * (6 * 1024 * 1024)
    response = client.post(
        "/wishes/upload",
        files={"file": ("bigfile.png", io.BytesIO(file_content), "image/png")},
    )
    assert response.status_code == 413
    data = response.json()
    assert data["type"] == "https://example.com/probs/file-too-large"
    assert "correlation_id" in data


def test_path_traversal_rejected():
    file_content = b"PDF" + b"\x00" * 100
    response = client.post(
        "/wishes/upload",
        files={"file": ("../../evil.pdf", io.BytesIO(file_content), "application/pdf")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["title"] == "Invalid file path"


def test_invalid_mime_type():
    file_content = b"NOT_A_PNG"
    response = client.post(
        "/wishes/upload",
        files={"file": ("fake.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["title"] == "Invalid file type"
