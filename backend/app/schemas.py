"""Pydantic request/response models."""
import re
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


# ---------- auth ----------
class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # e.g. {"role": "admin"} is rejected, not silently ignored
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- vehicles ----------
class VehicleBase(BaseModel):
    make: Name
    model: Name
    category: Name
    price: float = Field(gt=0, le=10_000_000)
    quantity: int = Field(ge=0, le=100_000)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _valid_color(cls, v: str | None) -> str | None:
        if v is not None and not _HEX.match(v):
            raise ValueError("color must be a hex value like #1A2B3C")
        return v


class VehicleCreate(VehicleBase):
    model_config = ConfigDict(extra="forbid")


class VehicleUpdate(BaseModel):
    """All fields optional (partial update)."""

    model_config = ConfigDict(extra="forbid")
    make: Name | None = None
    model: Name | None = None
    category: Name | None = None
    price: float | None = Field(default=None, gt=0, le=10_000_000)
    quantity: int | None = Field(default=None, ge=0, le=100_000)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = None

    _valid_color = field_validator("color")(VehicleBase._valid_color.__func__)  # type: ignore[attr-defined]


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    make: str
    model: str
    category: str
    price: float
    quantity: int
    reserved: int
    available: int
    year: int | None = None
    color: str | None = None


class SearchParams(BaseModel):
    make: str | None = None
    model: str | None = None
    category: str | None = None
    q: str | None = None
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    in_stock: bool = False
    sort: str = Field(default="newest", pattern="^(newest|price_asc|price_desc|name)$")
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _range_ok(self):
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price cannot be greater than max_price")
        return self


# ---------- inventory ----------
class RestockIn(BaseModel):
    quantity: int = Field(gt=0, le=10_000)


class PurchaseIn(BaseModel):
    hold_id: int | None = None


class HoldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_id: int
    status: str
    created_at: datetime
    expires_at: datetime


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    vehicle_id: int | None
    vehicle_label: str | None
    user_email: str | None
    delta: int
    amount: float | None
    detail: str | None
    created_at: datetime


# ---------- analytics ----------
class CategoryStat(BaseModel):
    category: str
    units: int
    value: float


class DayStat(BaseModel):
    date: str
    purchases: int
    revenue: float


class LowStockItem(BaseModel):
    id: int
    label: str
    available: int


class AnalyticsOut(BaseModel):
    vehicle_count: int
    units_in_stock: int
    units_reserved: int
    inventory_value: float
    units_sold: int
    revenue: float
    by_category: list[CategoryStat]
    purchases_by_day: list[DayStat]
    low_stock: list[LowStockItem]


# ---------- orders ----------
class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_id: int | None
    vehicle_label: str
    category: str | None
    color: str | None
    price: float
    from_hold: bool
    created_at: datetime


class AdminOrderOut(OrderOut):
    user_email: str
