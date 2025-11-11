import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.routes import wishes

TEST_MODE = bool(os.environ.get("PYTEST_RUNNING"))

if TEST_MODE:
    os.environ.setdefault("JWT_SECRET", "testsecret123456")

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET or len(JWT_SECRET) < 16:
    raise RuntimeError("JWT_SECRET missing or too short!")

# ---- FastAPI app ----
app = FastAPI(title="SecDev Course App", version="0.1.0")


# ---- Secret info endpoint ----
def get_secret_info():
    return {"length": len(JWT_SECRET)}


@app.get("/secret-info")
def secret_info():
    info = get_secret_info()
    return {"message": "Secret loaded safely", "secret_length": info["length"]}


# ---- Errors ----
class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


# ---- Health endpoint ----
@app.get("/health")
def health():
    return {"status": "ok"}


# ---- Demo DB ----
_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError("validation_error", "name must be 1..100 chars", 422)
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError("not_found", "item not found", 404)


# ---- Include wishes router ----


app.include_router(wishes.router)
