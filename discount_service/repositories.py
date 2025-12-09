# discount_service/repositories.py
from datetime import datetime, date
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models


class CampaignRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, campaign: models.Campaign) -> models.Campaign:
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def get(self, campaign_id: int) -> Optional[models.Campaign]:
        return (
            self.db.query(models.Campaign)
            .filter(models.Campaign.id == campaign_id)
            .first()
        )

    def delete(self, campaign: models.Campaign):
        self.db.delete(campaign)
        self.db.commit()

    def list_paginated(
        self, page: int, page_size: int
    ) -> Tuple[List[models.Campaign], int]:
        query = self.db.query(models.Campaign).order_by(models.Campaign.id.desc())
        total_items = query.count()
        items = (
            query.offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total_items

    def get_active_for_now(self, now: datetime) -> List[models.Campaign]:
        return (
            self.db.query(models.Campaign)
            .filter(
                models.Campaign.is_active.is_(True),
                models.Campaign.start_date <= now,
                models.Campaign.end_date >= now,
            )
            .order_by(models.Campaign.priority.desc(), models.Campaign.id.asc())
            .all()
        )

    def save(self, campaign: models.Campaign) -> models.Campaign:
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign


class DiscountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_discount_for_campaign(self, campaign_id: int) -> float:
        total = (
            self.db.query(func.coalesce(func.sum(models.DiscountRedemption.discount_amount), 0.0))
            .filter(models.DiscountRedemption.campaign_id == campaign_id)
            .scalar()
        )
        return float(total or 0.0)

    def get_usage_count_for_customer_today(
        self, campaign_id: int, customer_id: str
    ) -> int:
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())

        count = (
            self.db.query(func.count(models.DiscountRedemption.id))
            .filter(
                models.DiscountRedemption.campaign_id == campaign_id,
                models.DiscountRedemption.customer_id == customer_id,
                models.DiscountRedemption.created_at >= start,
                models.DiscountRedemption.created_at <= end,
            )
            .scalar()
        )
        return int(count or 0)

    def count_redemptions_for_campaign(self, campaign_id: int) -> int:
        count = (
            self.db.query(func.count(models.DiscountRedemption.id))
            .filter(models.DiscountRedemption.campaign_id == campaign_id)
            .scalar()
        )
        return int(count or 0)

    def create_redemption(
        self,
        campaign_id: int,
        customer_id: str,
        discount_amount: float,
        order_id: Optional[str] = None,
    ) -> models.DiscountRedemption:
        redemption = models.DiscountRedemption(
            campaign_id=campaign_id,
            customer_id=customer_id,
            discount_amount=discount_amount,
            order_id=order_id,
        )
        self.db.add(redemption)
        self.db.commit()
        self.db.refresh(redemption)
        return redemption
