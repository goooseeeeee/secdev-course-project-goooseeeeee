# test_wishes.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.wishes import _DB_WISHES, router


@pytest.fixture(autouse=True)
def clear_db():
    """Перед каждым тестом очищаем БД и сбрасываем счётчик."""
    _DB_WISHES.clear()
    global _ID_COUNTER
    _ID_COUNTER = 1
    yield


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ---------- ТЕСТЫ CRUD ----------


def test_create_wish(client):
    payload = {
        "title": "Ноутбук",
        "link": "https://example.com/laptop",
        "price_estimate": 1000.0,
        "notes": "Для работы",
        "category": "Техника",
    }
    response = client.post("/wishes/", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["title"] == "Ноутбук"
    assert len(_DB_WISHES) == 1


def test_list_wishes(client):
    # создаём несколько желаний
    wishes = [
        {"title": "Телефон", "price_estimate": 700, "category": "Техника"},
        {"title": "Путешествие", "price_estimate": 1500, "category": "Отдых"},
        {"title": "Книга", "price_estimate": 20, "category": "Развлечения"},
    ]
    for w in wishes:
        client.post("/wishes/", json=w)

    # без фильтров
    response = client.get("/wishes/")
    assert response.status_code == 200
    assert len(response.json()) == 3

    # фильтр по max_price
    response = client.get("/wishes/?max_price=100")
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Книга"

    # фильтр по категории
    response = client.get("/wishes/?category=Техника")
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Телефон"

    # сортировка по названию
    response = client.get("/wishes/?sort_by=title")
    titles = [w["title"] for w in response.json()]
    assert titles == sorted(titles)


def test_get_wish(client):
    wish = {"title": "Планшет", "price_estimate": 500}
    created = client.post("/wishes/", json=wish).json()

    # существующее желание
    response = client.get(f"/wishes/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Планшет"

    # несуществующее желание
    response = client.get("/wishes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wish not found"


def test_update_wish(client):
    wish = {"title": "Наушники", "price_estimate": 200}
    created = client.post("/wishes/", json=wish).json()

    updated_data = {"title": "AirPods", "price_estimate": 250}
    response = client.put(f"/wishes/{created['id']}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "AirPods"
    assert data["price_estimate"] == 250

    # несуществующий ID
    response = client.put("/wishes/999", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Wish not found"


def test_delete_wish(client):
    wish = {"title": "Камера", "price_estimate": 800}
    created = client.post("/wishes/", json=wish).json()

    # удаление существующего
    response = client.delete(f"/wishes/{created['id']}")
    assert response.status_code == 200
    assert response.json()["message"] == "Wish deleted"
    assert len(_DB_WISHES) == 0

    # повторное удаление
    response = client.delete(f"/wishes/{created['id']}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wish not found"
