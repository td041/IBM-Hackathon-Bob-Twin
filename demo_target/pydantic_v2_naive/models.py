"""Pydantic v2 models — naive migration output from bump-pydantic.

This is what you get AFTER running bump-pydantic without fixing the 4 trap patterns.
Each trap is labeled with the symptom it will cause during replay diff.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


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


# ── TRAP 3: __root__ model — BROKEN ──────────────────────────────────────────
# bump-pydantic removed __root__ but didn't convert to RootModel
# Result: endpoint expects array body but model is now a plain BaseModel → 422 error

class TagList(BaseModel):
    # MISSING: should be RootModel[list[str]]
    # bump-pydantic dropped __root__ → now this model has no fields → 422 on array input
    items: List[str] = []


class TagsResponse(BaseModel):
    product_id: int
    tags: List[str]
    count: int


# ── TRAP 4: each_item validator — BROKEN ─────────────────────────────────────
# bump-pydantic converted @validator → @field_validator but dropped each_item=True
# Result: validator runs on the whole list, not each item → invalid ratings pass through

class ReviewItem(BaseModel):
    product_id: int
    rating: int
    comment: str
    # NOTE: per-item rating validator intentionally removed here —
    # it was on BulkReviewRequest with each_item=True in v1, which v2 dropped


class BulkReviewRequest(BaseModel):
    reviews: List[ReviewItem]

    @field_validator("reviews")
    @classmethod
    def validate_reviews(cls, v):
        # BROKEN: v1 used @validator("reviews", each_item=True) which validated
        # each ReviewItem individually. In v2 each_item=True doesn't exist, so
        # bump-pydantic converted this to a list-level validator that does nothing
        # useful — individual rating bounds are never checked.
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
