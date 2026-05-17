"""Pydantic v2 models — naive migration output from bump-pydantic.

This is what you get AFTER running bump-pydantic without fixing the 4 trap patterns.
Each trap is labeled with the symptom it will cause during replay diff.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, RootModel, field_serializer, field_validator


# ── Control models (correctly migrated by bump-pydantic) ─────────────────────

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


# ── TRAP 1: Enum field — BROKEN ───────────────────────────────────────────────
# In v1, role was stored as string "ADMIN" in dict, and use_enum_values=True ensured
# serialization as plain string. In v2, bump-pydantic kept the Enum but:
#   1. Dropped use_enum_values=True from Config migration
#   2. Pydantic v2 model_dump() returns the Enum object, not the value
# FastAPI uses jsonable_encoder which calls .value on Enum — but only in some versions.
# The real v2 trap: Pydantic v2 serialize_as_any changed + enum serialization
# uses {"value":"ADMIN","name":"ADMIN"} when mode="python" is used via old FastAPI compat.
# We simulate this with a plain IntEnum-style approach to force the object output.

class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"


class UserWithRole(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    id: int
    name: str
    email: str
    role: Role


# ── TRAP 2: Decimal field — BROKEN ───────────────────────────────────────────
# bump-pydantic removed json_encoders (v1 only) but didn't add field_serializer
# Result: total serializes as "29.97" (string) instead of 29.97 (float)

class OrderCalculate(BaseModel):
    item_id: int
    quantity: int
    unit_price: Decimal

    @field_serializer("unit_price")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class OrderResult(BaseModel):
    item_id: int
    quantity: int
    unit_price: Decimal
    total: Decimal
    currency: str = "USD"

    @field_serializer("unit_price", "total")
    def serialize_decimals(self, value: Decimal) -> float:
        return float(value)


# ── TRAP 3: __root__ model — FIXED ────────────────────────────────────────────
# Converted to RootModel to accept array body directly

class TagList(RootModel[List[str]]):
    root: List[str]


class TagsResponse(BaseModel):
    product_id: int
    tags: List[str]
    count: int


# ── TRAP 4: each_item validator — FIXED ──────────────────────────────────────
# Manually iterate through list items to validate each rating

class ReviewItem(BaseModel):
    product_id: int
    rating: int
    comment: str

    @field_validator("rating")
    @classmethod
    def rating_must_be_valid(cls, v):
        if not (1 <= v <= 5):
            raise ValueError(f"rating must be between 1 and 5, got {v}")
        return v


class BulkReviewRequest(BaseModel):
    reviews: List[ReviewItem]

    @field_validator("reviews")
    @classmethod
    def validate_reviews(cls, v):
        # Validate each review item's rating bounds
        for review in v:
            if review.rating < 1 or review.rating > 5:
                raise ValueError(f"rating {review.rating} out of range")
        return v


class BulkReviewResponse(BaseModel):
    accepted: int
    rejected: int
    reviews: List[ReviewItem]


# ── Control models ────────────────────────────────────────────────────────────

class Order(BaseModel):
    id: int
    user_id: int
    item: str
    amount: Decimal

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> float:
        return float(value)
