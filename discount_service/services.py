# discount_service/services.py
from datetime import datetime
from typing import List

from . import models, schemas
from .repositories import CampaignRepository, DiscountRepository
from .discount_strategies import DiscountStrategyFactory


class DiscountService:
    def __init__(
        self,
        campaign_repo: CampaignRepository,
        discount_repo: DiscountRepository,
    ):
        self.campaign_repo = campaign_repo
        self.discount_repo = discount_repo

    def _is_customer_targeted(self, campaign: models.Campaign, customer_id: str) -> bool:
        if not campaign.targets:
            return True
        return any(t.customer_id == customer_id for t in campaign.targets)

    def _passes_usage_limits(
        self,
        campaign: models.Campaign,
        customer_id: str,
    ) -> bool:
        usage_today = self.discount_repo.get_usage_count_for_customer_today(
            campaign.id, customer_id
        )
        if usage_today >= campaign.max_transactions_per_customer_per_day:
            return False

        if campaign.max_uses_overall is not None:
            total_uses = self.discount_repo.count_redemptions_for_campaign(campaign.id)
            if total_uses >= campaign.max_uses_overall:
                return False

        return True

    def _passes_minimums(
        self,
        campaign: models.Campaign,
        cart_total: float,
        delivery_charge: float,
    ) -> bool:
        if campaign.min_cart_total is not None and cart_total < campaign.min_cart_total:
            return False
        if (
            campaign.min_delivery_charge is not None
            and delivery_charge < campaign.min_delivery_charge
        ):
            return False
        return True

    def _compute_discount(
        self,
        campaign: models.Campaign,
        cart_total: float,
        delivery_charge: float,
    ) -> float:
        spent = self.discount_repo.get_total_discount_for_campaign(campaign.id)
        remaining_budget = campaign.total_budget - spent
        if remaining_budget <= 0:
            return 0.0

        if campaign.discount_scope == models.DiscountScope.CART:
            base_amount = cart_total
        else:
            base_amount = delivery_charge

        strategy = DiscountStrategyFactory.get_strategy(campaign.discount_value_type)
        return strategy.compute(
            base_amount=base_amount,
            discount_value=campaign.discount_value,
            max_discount_amount=campaign.max_discount_amount,
            remaining_budget=remaining_budget,
        )

    def _to_campaign_out(self, camp: models.Campaign) -> schemas.CampaignOut:
        return schemas.CampaignOut(
            id=camp.id,
            name=camp.name,
            description=camp.description,
            code=camp.code,
            discount_scope=camp.discount_scope,
            discount_value_type=camp.discount_value_type,
            discount_value=camp.discount_value,
            max_discount_amount=camp.max_discount_amount,
            start_date=camp.start_date,
            end_date=camp.end_date,
            total_budget=camp.total_budget,
            min_cart_total=camp.min_cart_total,
            min_delivery_charge=camp.min_delivery_charge,
            max_transactions_per_customer_per_day=camp.max_transactions_per_customer_per_day,
            max_uses_overall=camp.max_uses_overall,
            allow_stack_with_other_discounts=camp.allow_stack_with_other_discounts,
            priority=camp.priority,
            is_active=camp.is_active,
            target_customer_ids=[t.customer_id for t in camp.targets],
        )

    def get_available_campaigns(
        self, req: schemas.DiscountCheckRequest
    ) -> List[schemas.AvailableCampaign]:
        now = datetime.utcnow()
        campaigns = self.campaign_repo.get_active_for_now(now)

        result: List[schemas.AvailableCampaign] = []

        for camp in campaigns:
            if not self._is_customer_targeted(camp, req.customer_id):
                continue

            if not self._passes_usage_limits(camp, req.customer_id):
                continue

            if not self._passes_minimums(camp, req.cart_total, req.delivery_charge):
                continue

            discount = self._compute_discount(camp, req.cart_total, req.delivery_charge)
            if discount <= 0:
                continue

            final_cart_total = req.cart_total
            final_delivery_charge = req.delivery_charge

            if camp.discount_scope == models.DiscountScope.CART:
                final_cart_total = max(req.cart_total - discount, 0.0)
            else:
                final_delivery_charge = max(req.delivery_charge - discount, 0.0)

            result.append(
                schemas.AvailableCampaign(
                    campaign=self._to_campaign_out(camp),
                    applicable_discount=discount,
                    final_cart_total=final_cart_total,
                    final_delivery_charge=final_delivery_charge,
                )
            )

        return result

    def apply_discount(self, req: schemas.DiscountApplyRequest) -> schemas.DiscountApplyResponse:
        now = datetime.utcnow()
        campaign = self.campaign_repo.get(req.campaign_id)
        if not campaign or not campaign.is_active:
            raise ValueError("Campaign not found or inactive")

        if not (campaign.start_date <= now <= campaign.end_date):
            raise ValueError("Campaign not active in current date range")

        if not self._is_customer_targeted(campaign, req.customer_id):
            raise ValueError("Customer not eligible for this campaign")

        if not self._passes_usage_limits(campaign, req.customer_id):
            raise ValueError("Usage limit exceeded for this campaign")

        if not self._passes_minimums(campaign, req.cart_total, req.delivery_charge):
            raise ValueError("Order does not meet minimum requirements")

        discount = self._compute_discount(
            campaign, req.cart_total, req.delivery_charge
        )
        if discount <= 0:
            raise ValueError("No discount applicable")

        final_cart_total = req.cart_total
        final_delivery_charge = req.delivery_charge
        if campaign.discount_scope == models.DiscountScope.CART:
            final_cart_total = max(req.cart_total - discount, 0.0)
        else:
            final_delivery_charge = max(req.delivery_charge - discount, 0.0)

        self.discount_repo.create_redemption(
            campaign_id=campaign.id,
            customer_id=req.customer_id,
            discount_amount=discount,
            order_id=req.order_id,
        )

        return schemas.DiscountApplyResponse(
            campaign_id=campaign.id,
            customer_id=req.customer_id,
            applied_discount=discount,
            final_cart_total=final_cart_total,
            final_delivery_charge=final_delivery_charge,
        )
