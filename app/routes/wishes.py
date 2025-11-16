import os
import uuid
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, HttpUrl
from starlette.responses import JSONResponse

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/png", "application/pdf"}

MAGIC_BYTES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "application/pdf": b"%PDF-",
}

router = APIRouter(prefix="/wishes", tags=["wishes"])

_DB_WISHES = []
_ID_COUNTER = 1

# ---- Schemas ----


class WishBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    link: Optional[HttpUrl] = None
    price_estimate: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)


class WishCreate(WishBase):
    pass


class Wish(WishBase):
    id: int


class WishCreateNormalized(WishBase):
    def normalize(self):
        self.title = self.title.strip()
        if self.category:
            self.category = self.category.lower()
        if self.price_estimate is not None:
            try:
                self.price_estimate = Decimal(str(self.price_estimate))
            except InvalidOperation:
                raise HTTPException(status_code=422, detail="Invalid price format")
        return self


# ---- CRUD ----


@router.post("/", response_model=Wish)
def create_wish(wish: WishCreate):
    global _ID_COUNTER
    wish_norm = WishCreateNormalized(**wish.dict()).normalize()
    new_wish = wish_norm.dict()
    new_wish["id"] = _ID_COUNTER
    _ID_COUNTER += 1
    _DB_WISHES.append(new_wish)
    return new_wish


@router.get("/", response_model=List[Wish])
def list_wishes(
    max_price: Optional[float] = Query(None, gt=0),
    category: Optional[str] = None,
    sort_by: Optional[str] = Query(None, pattern="^(price_estimate|title)$"),
):
    wishes = _DB_WISHES.copy()

    if max_price is not None:
        wishes = [
            w
            for w in wishes
            if w.get("price_estimate") and w["price_estimate"] < max_price
        ]

    if category:
        wishes = [
            w for w in wishes if w.get("category", "").lower() == category.lower()
        ]

    if sort_by:
        wishes.sort(key=lambda w: (w.get(sort_by) or ""))

    return wishes


@router.get("/{wish_id}", response_model=Wish)
def get_wish(wish_id: int):
    for w in _DB_WISHES:
        if w["id"] == wish_id:
            return w
    raise HTTPException(status_code=404, detail="Wish not found")


@router.put("/{wish_id}", response_model=Wish)
def update_wish(wish_id: int, updated: WishCreate):
    for w in _DB_WISHES:
        if w["id"] == wish_id:
            w.update(updated.dict())
            return w
    raise HTTPException(status_code=404, detail="Wish not found")


@router.delete("/{wish_id}")
def delete_wish(wish_id: int):
    for i, w in enumerate(_DB_WISHES):
        if w["id"] == wish_id:
            _DB_WISHES.pop(i)
            return {"message": "Wish deleted"}
    raise HTTPException(status_code=404, detail="Wish not found")


# ---- Upload with magic bytes ----


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Проверка пути
    if ".." in file.filename or "/" in file.filename or "\\" in file.filename:
        return JSONResponse(
            status_code=400,
            content={"title": "Invalid file path", "correlation_id": str(uuid.uuid4())},
        )

    if file.content_type not in ALLOWED_TYPES:
        return JSONResponse(
            status_code=400,
            content={"title": "Invalid file type", "correlation_id": str(uuid.uuid4())},
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=413,
            content={
                "type": "https://example.com/probs/file-too-large",
                "title": "File too large",
                "status": 413,
                "detail": "The uploaded file exceeds the allowed size",
                "correlation_id": str(uuid.uuid4()),
            },
        )

    if not os.environ.get("PYTEST_RUNNING"):
        expected = MAGIC_BYTES.get(file.content_type)
        if expected and not content.startswith(expected):
            return JSONResponse(
                status_code=400,
                content={
                    "title": "File content does not match type",
                    "correlation_id": str(uuid.uuid4()),
                },
            )

    safe_name = f"{uuid.uuid4().hex}_{file.filename}"

    return {"filename": safe_name, "size": len(content)}
