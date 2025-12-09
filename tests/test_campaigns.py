# tests/test_campaigns.py
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from discount_service.main import app

client = TestClient(app)


def test_create_and_list_campaign():
    now = datetime.utcnow()
    payload = {
        "name": "Cart 10 percent",
        "description": "10% off on cart",
        "code": "CART10",
        "discount_scope": "cart",
        "discount_value_type": "percent",
        "discount_value": 10.0,
        "max_discount_amount": 200.0,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=7)).isoformat(),
        "total_budget": 1000.0,
        "min_cart_total": 100.0,
        "min_delivery_charge": 0.0,
        "max_transactions_per_customer_per_day": 2,
        "max_uses_overall": 100,
        "allow_stack_with_other_discounts": False,
        "priority": 1,
        "target_customer_ids": ["cust1", "cust2"],
    }

    r = client.post("/campaigns", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["name"] == "Cart 10 percent"
    assert len(data["target_customer_ids"]) == 2

    r2 = client.get("/campaigns?page=1&page_size=10")
    assert r2.status_code == 200, r2.text
    page = r2.json()
    assert "items" in page
    assert page["page"] == 1
    assert page["page_size"] == 10
    assert page["total_items"] >= 1
    assert len(page["items"]) >= 1
