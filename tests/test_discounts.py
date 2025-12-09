# tests/test_discounts.py
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from discount_service.main import app

client = TestClient(app)


def create_sample_campaign():
    now = datetime.utcnow()
    payload = {
        "name": "Delivery 50 flat",
        "description": "50 off on delivery",
        "code": "DEL50",
        "discount_scope": "delivery",
        "discount_value_type": "flat",
        "discount_value": 50.0,
        "max_discount_amount": None,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
        "total_budget": 200.0,
        "min_cart_total": 0.0,
        "min_delivery_charge": 0.0,
        "max_transactions_per_customer_per_day": 1,
        "max_uses_overall": 10,
        "allow_stack_with_other_discounts": False,
        "priority": 10,
        "target_customer_ids": ["custX"],
    }
    r = client.post("/campaigns", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_available_and_apply_discount():
    campaign_id = create_sample_campaign()

    payload = {
        "customer_id": "custX",
        "cart_total": 500.0,
        "delivery_charge": 60.0,
    }
    r = client.post("/discounts/available", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) >= 1
    match = [c for c in data if c["campaign"]["id"] == campaign_id]
    assert match, "Expected our campaign to be in available discounts"
    assert match[0]["applicable_discount"] == 50.0
    assert match[0]["final_delivery_charge"] == 10.0

    apply_payload = {
        "campaign_id": campaign_id,
        "customer_id": "custX",
        "cart_total": 500.0,
        "delivery_charge": 60.0,
    }
    r2 = client.post("/discounts/apply", json=apply_payload)
    assert r2.status_code == 200, r2.text
    res = r2.json()
    assert res["applied_discount"] == 50.0
    assert res["final_delivery_charge"] == 10.0

    r3 = client.post("/discounts/apply", json=apply_payload)
    assert r3.status_code == 400
