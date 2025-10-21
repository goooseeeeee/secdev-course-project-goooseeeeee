from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, HttpUrl
from starlette.responses import JSONResponse

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/png", "application/pdf"}


router = APIRouter(prefix="/wishes", tags=["wishes"])

_DB_WISHES = []
_ID_COUNTER = 1


# ---- Pydantic-схемы ----
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


# ---- CRUD методы ----


@router.post("/", response_model=Wish)
def create_wish(wish: WishCreate):
    """
    Создать новое желание.
    """
    global _ID_COUNTER
    new_wish = wish.dict()
    new_wish["id"] = _ID_COUNTER
    _ID_COUNTER += 1
    _DB_WISHES.append(new_wish)
    return new_wish


@router.get("/", response_model=List[Wish])
def list_wishes(
    max_price: Optional[float] = Query(None, gt=0, description="Максимальная цена"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    sort_by: Optional[str] = Query(
        None, pattern="^(price_estimate|title)$", description="Сортировка по полю"
    ),
):
    """
    Получить список желаний с фильтрацией и сортировкой.
    """
    wishes = _DB_WISHES.copy()

    if max_price is not None:
        wishes = [
            w
            for w in wishes
            if w.get("price_estimate") and w["price_estimate"] < max_price
        ]

    if category:
        wishes = [w for w in wishes if w.get("category") == category]

    if sort_by:
        wishes.sort(key=lambda w: (w.get(sort_by) or ""))

    return wishes


@router.get("/{wish_id}", response_model=Wish)
def get_wish(wish_id: int):
    """
    Получить конкретное желание по ID.
    """
    for w in _DB_WISHES:
        if w["id"] == wish_id:
            return w
    raise HTTPException(status_code=404, detail="Wish not found")


@router.put("/{wish_id}", response_model=Wish)
def update_wish(wish_id: int, updated: WishCreate):
    """
    Обновить данные о желании.
    """
    for w in _DB_WISHES:
        if w["id"] == wish_id:
            w.update(updated.dict())
            return w
    raise HTTPException(status_code=404, detail="Wish not found")


@router.delete("/{wish_id}")
def delete_wish(wish_id: int):
    """
    Удалить желание.
    """
    for i, w in enumerate(_DB_WISHES):
        if w["id"] == wish_id:
            _DB_WISHES.pop(i)
            return {"message": "Wish deleted"}
    raise HTTPException(status_code=404, detail="Wish not found")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if ".." in file.filename or "/" in file.filename or "\\" in file.filename:
        return JSONResponse(
            status_code=400,
            content={"title": "Invalid file path", "correlation_id": "xxx"},
        )

    if file.content_type not in ALLOWED_TYPES:
        return JSONResponse(
            status_code=400,
            content={"title": "Invalid file type", "correlation_id": "xxx"},
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
                "correlation_id": "xxx",
            },
        )

    return {"filename": file.filename, "size": len(content)}
