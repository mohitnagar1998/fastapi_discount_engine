# discount_service/main.py
import math

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from typing import List

from .database import Base, engine, get_db
from . import models, schemas
from .repositories import CampaignRepository, DiscountRepository
from .services import DiscountService

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Campaign Management & Discount Service",
    description="APIs for managing discount campaigns and resolving applicable discounts.",
    version="2.0.0",
)


def get_discount_service(db: Session = Depends(get_db)) -> DiscountService:
    camp_repo = CampaignRepository(db)
    disc_repo = DiscountRepository(db)
    return DiscountService(camp_repo, disc_repo)


@app.post("/campaigns", response_model=schemas.CampaignOut)
def create_campaign(
    campaign_in: schemas.CampaignCreate,
    db: Session = Depends(get_db),
):
    camp_repo = CampaignRepository(db)
    discount_repo = DiscountRepository(db)
    service = DiscountService(camp_repo, discount_repo)

    campaign = models.Campaign(
        name=campaign_in.name,
        description=campaign_in.description,
        code=campaign_in.code,
        discount_scope=campaign_in.discount_scope,
        discount_value_type=campaign_in.discount_value_type,
        discount_value=campaign_in.discount_value,
        max_discount_amount=campaign_in.max_discount_amount,
        start_date=campaign_in.start_date,
        end_date=campaign_in.end_date,
        total_budget=campaign_in.total_budget,
        min_cart_total=campaign_in.min_cart_total,
        min_delivery_charge=campaign_in.min_delivery_charge,
        max_transactions_per_customer_per_day=campaign_in.max_transactions_per_customer_per_day,
        max_uses_overall=campaign_in.max_uses_overall,
        allow_stack_with_other_discounts=campaign_in.allow_stack_with_other_discounts,
        priority=campaign_in.priority,
        is_active=True,
    )

    if campaign_in.target_customer_ids:
        campaign.targets = [
            models.CampaignTargetCustomer(customer_id=c_id)
            for c_id in campaign_in.target_customer_ids
        ]

    campaign = camp_repo.create(campaign)
    return service._to_campaign_out(campaign)


@app.get("/campaigns", response_model=schemas.CampaignPage)
def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    camp_repo = CampaignRepository(db)
    discount_repo = DiscountRepository(db)
    service = DiscountService(camp_repo, discount_repo)

    items, total_items = camp_repo.list_paginated(page, page_size)
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items else 1

    return schemas.CampaignPage(
        items=[service._to_campaign_out(c) for c in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


@app.get("/campaigns/{campaign_id}", response_model=schemas.CampaignOut)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    camp_repo = CampaignRepository(db)
    discount_repo = DiscountRepository(db)
    service = DiscountService(camp_repo, discount_repo)

    campaign = camp_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return service._to_campaign_out(campaign)


@app.put("/campaigns/{campaign_id}", response_model=schemas.CampaignOut)
def update_campaign(
    campaign_id: int,
    campaign_in: schemas.CampaignUpdate,
    db: Session = Depends(get_db),
):
    camp_repo = CampaignRepository(db)
    discount_repo = DiscountRepository(db)
    service = DiscountService(camp_repo, discount_repo)

    campaign = camp_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.name = campaign_in.name
    campaign.description = campaign_in.description
    campaign.code = campaign_in.code
    campaign.discount_scope = campaign_in.discount_scope
    campaign.discount_value_type = campaign_in.discount_value_type
    campaign.discount_value = campaign_in.discount_value
    campaign.max_discount_amount = campaign_in.max_discount_amount
    campaign.start_date = campaign_in.start_date
    campaign.end_date = campaign_in.end_date
    campaign.total_budget = campaign_in.total_budget
    campaign.min_cart_total = campaign_in.min_cart_total
    campaign.min_delivery_charge = campaign_in.min_delivery_charge
    campaign.max_transactions_per_customer_per_day = (
        campaign_in.max_transactions_per_customer_per_day
    )
    campaign.max_uses_overall = campaign_in.max_uses_overall
    campaign.allow_stack_with_other_discounts = (
        campaign_in.allow_stack_with_other_discounts
    )
    campaign.priority = campaign_in.priority
    campaign.is_active = campaign_in.is_active

    campaign.targets.clear()
    if campaign_in.target_customer_ids:
        for cid in campaign_in.target_customer_ids:
            campaign.targets.append(models.CampaignTargetCustomer(customer_id=cid))

    campaign = camp_repo.save(campaign)
    return service._to_campaign_out(campaign)


@app.delete("/campaigns/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    camp_repo = CampaignRepository(db)
    campaign = camp_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    camp_repo.delete(campaign)
    return


@app.post("/discounts/available", response_model=List[schemas.AvailableCampaign])
def get_available_discounts(
    req: schemas.DiscountCheckRequest,
    service: DiscountService = Depends(get_discount_service),
):
    return service.get_available_campaigns(req)


@app.post("/discounts/apply", response_model=schemas.DiscountApplyResponse)
def apply_discount(
    req: schemas.DiscountApplyRequest,
    service: DiscountService = Depends(get_discount_service),
):
    try:
        return service.apply_discount(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
