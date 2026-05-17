"""FastAPI routes — naively migrated to Pydantic v2 (4 traps still broken)."""

from decimal import Decimal
from typing import List

from fastapi import APIRouter, HTTPException

from .models import (
    BulkReviewRequest,
    BulkReviewResponse,
    Order,
    OrderCalculate,
    OrderResult,
    ReviewItem,
    Role,
    TagList,
    TagsResponse,
    UserCreate,
    UserSimple,
    UserUpdate,
    UserWithRole,
)

router = APIRouter()

_INITIAL_USERS = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "ADMIN"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "USER"},
    3: {"id": 3, "name": "Carol", "email": "carol@example.com", "role": "VIEWER"},
}
_users: dict[int, dict] = {k: dict(v) for k, v in _INITIAL_USERS.items()}
_next_user_id = 4

_orders: dict[int, list] = {
    1: [{"id": 1, "user_id": 1, "item": "Widget A", "amount": Decimal("9.99")}],
    2: [{"id": 2, "user_id": 2, "item": "Widget B", "amount": Decimal("19.99")}],
}

_product_tags: dict[int, list] = {
    1: ["electronics", "sale"],
    2: ["books", "bestseller", "fiction"],
}


# ── CONTROL endpoints (all correctly migrated) ────────────────────────────────

@router.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0-pydantic-v2-naive"}


@router.get("/users", response_model=List[UserSimple])
def list_users():
    return [UserSimple(**u) for u in _users.values()]


@router.post("/users", response_model=UserSimple, status_code=201)
def create_user(body: UserCreate):
    global _next_user_id
    user = {"id": _next_user_id, "name": body.name, "email": body.email, "role": "USER"}
    _users[_next_user_id] = user
    _next_user_id += 1
    return UserSimple(**user)


@router.put("/users/{user_id}", response_model=UserSimple)
def update_user(user_id: int, body: UserUpdate):
    if user_id not in _users:
        raise HTTPException(status_code=404, detail="user not found")
    user = _users[user_id]
    if body.name is not None:
        user["name"] = body.name
    if body.email is not None:
        user["email"] = body.email
    return UserSimple(**user)


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    if user_id not in _users:
        raise HTTPException(status_code=404, detail="user not found")
    del _users[user_id]
    return {"deleted": user_id}


@router.get("/users/{user_id}/orders", response_model=List[Order])
def get_user_orders(user_id: int):
    if user_id not in _users:
        raise HTTPException(status_code=404, detail="user not found")
    return [Order(**o) for o in _orders.get(user_id, [])]


@router.post("/admin/reset", include_in_schema=False)
def reset_state():
    global _users, _next_user_id
    _users = {k: dict(v) for k, v in _INITIAL_USERS.items()}
    _next_user_id = 4
    return {"reset": True}


# ── TRAP endpoints (broken after naive migration) ─────────────────────────────

@router.get("/users/{user_id}")
def get_user(user_id: int):
    """TRAP 1 — naive migration: developer dropped response_model and returns
    user.model_dump() directly, expecting Pydantic v2 to produce JSON-ready
    output. Combined with the custom model_dump override on UserWithRole,
    role now leaks out as {"name":"ADMIN","value":"ADMIN"} instead of v1's
    plain string "ADMIN"."""
    if user_id not in _users:
        raise HTTPException(status_code=404, detail="user not found")
    return UserWithRole(**_users[user_id]).model_dump()


@router.post("/orders/calculate", response_model=OrderResult)
def calculate_order(body: OrderCalculate):
    """TRAP 2 — Pydantic v2 without field_serializer serializes Decimal as string."""
    total = body.unit_price * body.quantity
    return OrderResult(
        item_id=body.item_id,
        quantity=body.quantity,
        unit_price=body.unit_price,
        total=total,
    )


@router.post("/products/tags", response_model=TagsResponse)
def set_product_tags(product_id: int, body: TagList):
    """TRAP 3 — TagList now uses RootModel to accept array body directly."""
    tags = list(body.root)
    _product_tags[product_id] = tags
    return TagsResponse(product_id=product_id, tags=tags, count=len(tags))


@router.post("/reviews/bulk", response_model=BulkReviewResponse)
def bulk_reviews(body: BulkReviewRequest):
    """TRAP 4 — each_item validator no-ops; out-of-range ratings silently pass."""
    return BulkReviewResponse(
        accepted=len(body.reviews),
        rejected=0,
        reviews=body.reviews,
    )
