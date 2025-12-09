# discount_service/discount_strategies.py
from abc import ABC, abstractmethod
from typing import Optional

from .models import DiscountValueType


class DiscountStrategy(ABC):
    @abstractmethod
    def compute(
        self,
        base_amount: float,
        discount_value: float,
        max_discount_amount: Optional[float],
        remaining_budget: float,
    ) -> float:
        ...


class PercentDiscountStrategy(DiscountStrategy):
    def compute(
        self,
        base_amount: float,
        discount_value: float,
        max_discount_amount: Optional[float],
        remaining_budget: float,
    ) -> float:
        if base_amount <= 0:
            return 0.0
        discount = base_amount * (discount_value / 100.0)
        if max_discount_amount is not None:
            discount = min(discount, max_discount_amount)
        discount = min(discount, remaining_budget)
        return max(discount, 0.0)


class FlatDiscountStrategy(DiscountStrategy):
    def compute(
        self,
        base_amount: float,
        discount_value: float,
        max_discount_amount: Optional[float],
        remaining_budget: float,
    ) -> float:
        if base_amount <= 0:
            return 0.0
        discount = discount_value
        if max_discount_amount is not None:
            discount = min(discount, max_discount_amount)
        discount = min(discount, remaining_budget)
        return max(discount, 0.0)


class DiscountStrategyFactory:
    _percent_strategy = PercentDiscountStrategy()
    _flat_strategy = FlatDiscountStrategy()

    @classmethod
    def get_strategy(cls, value_type: DiscountValueType) -> DiscountStrategy:
        if value_type == DiscountValueType.PERCENT:
            return cls._percent_strategy
        return cls._flat_strategy
