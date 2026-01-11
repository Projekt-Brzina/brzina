from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..db import get_pool

router = APIRouter(prefix="/example", tags=["example"])


class ExampleItem(BaseModel):
    id: int | None = None
    name: str


@router.get("/", response_model=list[ExampleItem])
async def list_items():
    # For now, return hard-coded data; later, fetch from DB
    return [
        ExampleItem(id=1, name="item-1"),
        ExampleItem(id=2, name="item-2"),
    ]


@router.post("/", response_model=ExampleItem)
async def create_item(item: ExampleItem):
    # Example: pretend to save to DB
    return ExampleItem(id=123, name=item.name)