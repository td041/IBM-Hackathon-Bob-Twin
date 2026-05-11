"""Pydantic v1 models for the demo target application.

Contains 4 trap patterns that bump-pydantic does NOT handle automatically.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator


# ── Control models (bump-pydantic handles these fine) ────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class UserSimple(BaseModel):
    id: int
    name: str
    email: str


# ── TRAP 1: Enum field ────────────────────────────────────────────────────────
# Pydantic v1: role serializes as plain string "ADMIN"
# Naive v2 migration: role serializes as {"name": "ADMIN", "value": "ADMIN"}
# Fix needed: model_config = ConfigDict(use_enum_values=True)

class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"


class UserWithRole(BaseModel):
    id: int
    name: str
    email: str
    role: Role

    class Config:
        use_enum_values = True  # v1 — ensures "ADMIN" not Role.ADMIN in output


# ── TRAP 2: Decimal field ─────────────────────────────────────────────────────
# Pydantic v1: Decimal serializes as float 12.50
# Naive v2 migration: Decimal serializes as string "12.50"
# Fix needed: custom json_encoder or field_serializer

class OrderCalculate(BaseModel):
    item_id: int
    quantity: int
    unit_price: Decimal

    class Config:
        json_encoders = {Decimal: float}  # v1 — ensures float serialization


class OrderResult(BaseModel):
    item_id: int
    quantity: int
    unit_price: Decimal
    total: Decimal
    currency: str = "USD"

    class Config:
        json_encoders = {Decimal: float}


# ── TRAP 3: __root__ model ────────────────────────────────────────────────────
# Pydantic v1: TagList wraps list[str] as root model
# Naive v2 migration: import error or shape change (RootModel)
# Fix needed: class TagList(RootModel[list[str]]): ...

class TagList(BaseModel):
    __root__: List[str]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


class TagsResponse(BaseModel):
    product_id: int
    tags: List[str]
    count: int


# ── TRAP 4: each_item validator ───────────────────────────────────────────────
# Pydantic v1: @validator(each_item=True) validates each list element
# Naive v2 migration: validator silently no-ops; invalid data passes through
# Fix needed: @field_validator with mode='before', iterate manually

class ReviewItem(BaseModel):
    product_id: int
    rating: int
    comment: str

    @validator("rating")
    def rating_must_be_valid(cls, v):
        if not (1 <= v <= 5):
            raise ValueError(f"rating must be between 1 and 5, got {v}")
        return v


class BulkReviewRequest(BaseModel):
    reviews: List[ReviewItem]

    @validator("reviews", each_item=True)
    def validate_each_review(cls, v):
        if v.rating < 1 or v.rating > 5:
            raise ValueError(f"rating {v.rating} out of range")
        return v


class BulkReviewResponse(BaseModel):
    accepted: int
    rejected: int
    reviews: List[ReviewItem]


# ── Control models for user CRUD ──────────────────────────────────────────────

class Order(BaseModel):
    id: int
    user_id: int
    item: str
    amount: Decimal

    class Config:
        json_encoders = {Decimal: float}
