# discount_service/models.py
from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class DiscountScope(str, enum.Enum):
    CART = "cart"
    DELIVERY = "delivery"


class DiscountValueType(str, enum.Enum):
    PERCENT = "percent"
    FLAT = "flat"


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    code = Column(String, unique=True, nullable=True, index=True)

    discount_scope = Column(Enum(DiscountScope), nullable=False)
    discount_value_type = Column(Enum(DiscountValueType), nullable=False)
    discount_value = Column(Float, nullable=False)
    max_discount_amount = Column(Float, nullable=True)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    total_budget = Column(Float, nullable=False)

    min_cart_total = Column(Float, nullable=True)
    min_delivery_charge = Column(Float, nullable=True)

    max_transactions_per_customer_per_day = Column(Integer, nullable=False, default=1)
    max_uses_overall = Column(Integer, nullable=True)

    allow_stack_with_other_discounts = Column(Boolean, default=False)

    priority = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, default=True, nullable=False)

    targets = relationship(
        "CampaignTargetCustomer",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    redemptions = relationship(
        "DiscountRedemption",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class CampaignTargetCustomer(Base):
    __tablename__ = "campaign_target_customers"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(
        Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    customer_id = Column(String, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("campaign_id", "customer_id", name="uq_campaign_customer"),
    )

    campaign = relationship("Campaign", back_populates="targets")


class DiscountRedemption(Base):
    __tablename__ = "discount_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(
        Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    customer_id = Column(String, nullable=False, index=True)
    discount_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    order_id = Column(String, nullable=True, index=True)

    campaign = relationship("Campaign", back_populates="redemptions")
