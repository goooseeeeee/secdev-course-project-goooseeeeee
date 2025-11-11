import importlib
import io

import pytest
from fastapi.testclient import TestClient


# ---------------------------
# Тест secret_info
# ---------------------------
def test_secret_info(monkeypatch):

    monkeypatch.setenv("JWT_SECRET", "x" * 32)

    import app.main

    importlib.reload(app.main)

    from app.main import app

    client = TestClient(app)

    response = client.get("/secret-info")
    assert response.status_code == 200
    data = response.json()
    assert data["secret_length"] == 32


# ---------------------------
# Тест на отсутствие секретного ключа
# ---------------------------
def test_missing_secret(monkeypatch):

    monkeypatch.delenv("JWT_SECRET", raising=False)

    import app.main

    with pytest.raises(RuntimeError) as exc_info:
        importlib.reload(app.main)

    assert "JWT_SECRET missing" in str(exc_info.value)


# ---------------------------
# Пример теста загрузки файла (если есть эндпоинт /wishes/upload)
# ---------------------------
def test_valid_file_upload(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("PYTEST_RUNNING", "1")

    import app.main

    importlib.reload(app.main)
    from app.main import app

    client = TestClient(app)

    file_content = b"PNG" + b"\x00" * 1000
    response = client.post(
        "/wishes/upload",
        files={"file": ("test.png", io.BytesIO(file_content), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert data["size"] == len(file_content)
