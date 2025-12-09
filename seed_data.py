# seed_data.py
from datetime import datetime, timedelta

from discount_service.database import Base, engine, SessionLocal
from discount_service import models


def get_or_create_campaign(db, code: str, defaults: dict) -> models.Campaign:
    """
    Simple helper so we don't create duplicates if you run the script multiple times.
    Looks up by `code`. If exists, returns it. Else creates a new one.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.code == code).first()
    if campaign:
        print(f"Campaign with code '{code}' already exists (id={campaign.id}). Skipping create.")
        return campaign

    campaign = models.Campaign(code=code, **defaults)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    print(f"Created campaign '{campaign.name}' with id={campaign.id} and code='{campaign.code}'")
    return campaign


def main():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # 1) 10% off on cart, capped at 200, min cart 500, for ALL customers
        cart10_defaults = {
            "name": "Cart 10% OFF",
            "description": "Get 10% off on your cart up to ₹200.",
            "discount_scope": models.DiscountScope.CART,
            "discount_value_type": models.DiscountValueType.PERCENT,
            "discount_value": 10.0,
            "max_discount_amount": 200.0,
            "start_date": now - timedelta(days=1),
            "end_date": now + timedelta(days=30),
            "total_budget": 5000.0,
            "min_cart_total": 500.0,
            "min_delivery_charge": None,
            "max_transactions_per_customer_per_day": 2,
            "max_uses_overall": 500,
            "allow_stack_with_other_discounts": False,
            "priority": 5,
            "is_active": True,
        }
        cart10 = get_or_create_campaign(db, code="CART10", defaults=cart10_defaults)

        # 2) Flat ₹50 off on delivery, no min cart, only for specific customers
        del50_defaults = {
            "name": "Delivery ₹50 OFF",
            "description": "Flat ₹50 off on delivery charges.",
            "discount_scope": models.DiscountScope.DELIVERY,
            "discount_value_type": models.DiscountValueType.FLAT,
            "discount_value": 50.0,
            "max_discount_amount": None,
            "start_date": now - timedelta(days=1),
            "end_date": now + timedelta(days=7),
            "total_budget": 1000.0,
            "min_cart_total": 0.0,
            "min_delivery_charge": 40.0,
            "max_transactions_per_customer_per_day": 1,
            "max_uses_overall": 100,
            "allow_stack_with_other_discounts": False,
            "priority": 10,
            "is_active": True,
        }
        del50 = get_or_create_campaign(db, code="DEL50", defaults=del50_defaults)

        # Attach target customers to DEL50 (custA, custB only)
        if not del50.targets:
            del50.targets = [
                models.CampaignTargetCustomer(customer_id="custA"),
                models.CampaignTargetCustomer(customer_id="custB"),
            ]
            db.add(del50)
            db.commit()
            print("Added target customers [custA, custB] to DEL50 campaign.")

        # 3) High priority: 20% off cart, but min cart 1500, small budget
        cart20_defaults = {
            "name": "Cart 20% OFF (Big Spenders)",
            "description": "20% off on cart for big orders (min ₹1500), max ₹400 off.",
            "discount_scope": models.DiscountScope.CART,
            "discount_value_type": models.DiscountValueType.PERCENT,
            "discount_value": 20.0,
            "max_discount_amount": 400.0,
            "start_date": now - timedelta(days=1),
            "end_date": now + timedelta(days=5),
            "total_budget": 3000.0,
            "min_cart_total": 1500.0,
            "min_delivery_charge": None,
            "max_transactions_per_customer_per_day": 1,
            "max_uses_overall": 50,
            "allow_stack_with_other_discounts": False,
            "priority": 20,
            "is_active": True,
        }
        cart20 = get_or_create_campaign(db, code="CART20BIG", defaults=cart20_defaults)

        print("\nSeeding complete ✅")
        print("Sample campaigns:")
        print(f"- {cart10.id}: {cart10.name} (code={cart10.code})")
        print(f"- {del50.id}: {del50.name} (code={del50.code})")
        print(f"- {cart20.id}: {cart20.name} (code={cart20.code})")

    finally:
        db.close()


if __name__ == "__main__":
    main()
