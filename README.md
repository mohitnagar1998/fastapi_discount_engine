# FastAPI Discount Engine

This project is a backend service built with FastAPI and SQLAlchemy to manage discount campaigns and apply offers to customer carts.  
It includes APIs to create, update, list, and delete campaigns, and to calculate applicable discounts for users.

---

## Features

- Create and manage discount campaigns  
- Apply flat or percentage-based discounts  
- Validate campaign rules like date, limits, and eligibility  
- Target specific customers or apply globally  
- Supports pagination for campaign listing  
- Modular design using repository and strategy patterns  

---

## Project Structure

```
fastapi_discount_engine/
│
├── discount_service/
│   ├── main.py                # FastAPI app entry point
│   ├── models.py              # Database models
│   ├── schemas.py             # Request/response schemas
│   ├── database.py            # Database setup
│   ├── repositories.py        # Repository layer for CRUD operations
│   ├── services.py            # Business logic and validation
│   └── discount_strategies.py # Strategy pattern for discount types
│
├── tests/
│   ├── test_campaigns.py
│   └── test_discounts.py
│
├── seed_data.py               # Script to insert sample data
├── requirements.txt
└── README.md
```

---

## Setup Instructions

1. Clone the repository  
   ```bash
   git clone https://github.com/mohitnagar1998/fastapi-discount-engine.git
   cd fastapi-discount-engine
   ```

2. Create and activate a virtual environment  
   ```bash
   python -m venv venv
   venv\Scripts\activate      # On Windows
   # or
   source venv/bin/activate     # On Linux/Mac
   ```

3. Install dependencies  
   ```bash
   pip install -r requirements.txt
   ```

4. Seed sample data  
   ```bash
   python seed_data.py
   ```

   This creates a local SQLite database with sample campaigns like:
   - CART10 (10% off cart, max ₹200)
   - DEL50 (₹50 off delivery for custA, custB)
   - CART20BIG (20% off on cart above ₹1500)

5. Start the server  
   ```bash
   uvicorn discount_service.main:app --reload
   ```

   Open:  
   http://127.0.0.1:8000/docs for Swagger UI  
   http://127.0.0.1:8000/redoc for ReDoc

---

## Running Tests

```bash
python -m pytest
```

If everything is correct, you’ll see something like:

```
=================== 2 passed in 1.23s ===================
```

---

## API Documentation

### Campaign APIs

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | /campaigns | Create a new campaign |
| GET | /campaigns | List campaigns (paginated) |
| GET | /campaigns/{id} | Get a campaign by ID |
| PUT | /campaigns/{id} | Update a campaign |
| DELETE | /campaigns/{id} | Delete a campaign |

Example request:

```json
POST /campaigns
{
  "name": "Cart 10% OFF",
  "description": "Get 10% off on cart up to ₹200.",
  "code": "CART10",
  "discount_scope": "cart",
  "discount_value_type": "percent",
  "discount_value": 10,
  "max_discount_amount": 200,
  "start_date": "2025-01-01T00:00:00Z",
  "end_date": "2025-02-01T00:00:00Z",
  "total_budget": 5000,
  "min_cart_total": 500,
  "priority": 5
}
```

---

### Discount APIs

| Method | Endpoint | Description |
|---------|-----------|-------------|
| POST | /discounts/available | Get applicable campaigns for a given cart |
| POST | /discounts/apply | Apply a specific campaign and calculate the discount |

Example request to check available discounts:

```json
POST /discounts/available
{
  "customer_id": "custA",
  "cart_total": 2000,
  "delivery_charge": 60
}
```

Example response:

```json
[
  {
    "campaign": {
      "id": 3,
      "name": "Cart 20% OFF (Big Spenders)",
      "discount_scope": "cart",
      "discount_value_type": "percent",
      "discount_value": 20.0,
      "max_discount_amount": 400.0
    },
    "applicable_discount": 400.0,
    "final_cart_total": 1600.0,
    "final_delivery_charge": 60.0
  }
]
```

---

## Tech Stack

- Python 3.8+  
- FastAPI  
- SQLAlchemy  
- Pydantic v2  
- SQLite  
- Uvicorn  
- Pytest  

---

## Author

Mohit Nagar  
Software Engineer at Venera Technologies  
LinkedIn: https://www.linkedin.com/in/mohitnagar1998/  
GitHub: https://github.com/mohitnagar1998

---
