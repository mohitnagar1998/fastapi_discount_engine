# discount_service/schemas.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .models import DiscountScope, DiscountValueType


class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    code: Optional[str] = Field(
        None, min_length=3, max_length=50, description="Optional coupon code"
    )

    discount_scope: DiscountScope
    discount_value_type: DiscountValueType

    discount_value: float = Field(..., gt=0)
    max_discount_amount: Optional[float] = Field(None, gt=0)

    start_date: datetime
    end_date: datetime

    total_budget: float = Field(..., gt=0)

    min_cart_total: Optional[float] = Field(None, ge=0)
    min_delivery_charge: Optional[float] = Field(None, ge=0)

    max_transactions_per_customer_per_day: int = Field(..., gt=0)
    max_uses_overall: Optional[int] = Field(None, gt=0)

    allow_stack_with_other_discounts: bool = False
    priority: int = Field(0)

    target_customer_ids: Optional[List[str]] = None

    @validator("end_date")
    def validate_dates(cls, v, values):
        start = values.get("start_date")
        if start and v <= start:
            raise ValueError("end_date must be after start_date")
        return v

    @validator("discount_value")
    def validate_discount_value(cls, v, values):
        dtype = values.get("discount_value_type")
        if dtype == DiscountValueType.PERCENT and not (0 < v <= 100):
            raise ValueError("Percent discount_value must be in (0, 100].")
        return v

    @validator("max_discount_amount")
    def validate_max_discount_amount(cls, v, values):
        if v is None:
            return v
        total_budget = values.get("total_budget")
        if total_budget is not None and v > total_budget:
            raise ValueError("max_discount_amount cannot exceed total_budget.")
        return v


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(CampaignBase):
    is_active: bool = True


class CampaignOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    code: Optional[str]

    discount_scope: DiscountScope
    discount_value_type: DiscountValueType
    discount_value: float
    max_discount_amount: Optional[float]

    start_date: datetime
    end_date: datetime

    total_budget: float
    min_cart_total: Optional[float]
    min_delivery_charge: Optional[float]

    max_transactions_per_customer_per_day: int
    max_uses_overall: Optional[int]
    allow_stack_with_other_discounts: bool
    priority: int
    is_active: bool

    target_customer_ids: List[str] = []

    class Config:
        orm_mode = True


class CampaignPage(BaseModel):
    items: List[CampaignOut]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class DiscountCheckRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    cart_total: float = Field(..., ge=0)
    delivery_charge: float = Field(..., ge=0)


class AvailableCampaign(BaseModel):
    campaign: CampaignOut
    applicable_discount: float
    final_cart_total: float
    final_delivery_charge: float


class DiscountApplyRequest(DiscountCheckRequest):
    campaign_id: int
    order_id: Optional[str] = None


class DiscountApplyResponse(BaseModel):
    campaign_id: int
    customer_id: str
    applied_discount: float
    final_cart_total: float
    final_delivery_charge: float
