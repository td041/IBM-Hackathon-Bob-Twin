"""Deterministic seed script — generates ~40 HTTP interactions hitting every endpoint 3x+.

Run against the Pydantic v1 app on localhost:8001 before capture_baseline.
Usage: python scripts/seed_demo_traffic.py
"""

import requests

BASE = "http://localhost:8001"
_S = None


def _client():
    global _S
    if _S is None:
        _S = requests.Session()
    return _S


def _get(path):
    return _client().get(BASE + path, timeout=10.0)


def _post(path, json=None):
    return _client().post(BASE + path, json=json, timeout=10.0)


def _put(path, json=None):
    return _client().put(BASE + path, json=json, timeout=10.0)


def _delete(path):
    return _client().delete(BASE + path, timeout=10.0)


def run() -> None:
    global _S
    _S = requests.Session()

    # Reset to deterministic initial state before capturing
    _post("/admin/reset")

    # ── Control: health ───────────────────────────────────────────────
    for _ in range(3):
        _get("/health")

    # ── Control: list users ───────────────────────────────────────────
    for _ in range(3):
        _get("/users")

    # ── Control: create users ─────────────────────────────────────────
    _post("/users", {"name": "Dave", "email": "dave@example.com"})
    _post("/users", {"name": "Eve", "email": "eve@example.com"})
    _post("/users", {"name": "Frank", "email": "frank@example.com"})

    # ── Control: update user ──────────────────────────────────────────
    _put("/users/1", {"name": "Alice Updated"})
    _put("/users/2", {"email": "bob2@example.com"})
    _put("/users/3", {"name": "Carol Updated", "email": "carol2@example.com"})

    # ── Control: user orders ──────────────────────────────────────────
    for user_id in [1, 2, 1]:
        _get(f"/users/{user_id}/orders")

    # ── Control: delete user ──────────────────────────────────────────
    r1 = _post("/users", {"name": "Temp1", "email": "t1@example.com"})
    r2 = _post("/users", {"name": "Temp2", "email": "t2@example.com"})
    r3 = _post("/users", {"name": "Temp3", "email": "t3@example.com"})
    for r in [r1, r2, r3]:
        if r.status_code == 201:
            uid = r.json()["id"]
            _delete(f"/users/{uid}")

    # ── TRAP 1: Enum serialization — GET /users/{id} ──────────────────
    for user_id in [1, 2, 3]:
        _get(f"/users/{user_id}")

    # ── TRAP 2: Decimal serialization — POST /orders/calculate ────────
    _post("/orders/calculate", {"item_id": 1, "quantity": 2, "unit_price": "9.99"})
    _post("/orders/calculate", {"item_id": 2, "quantity": 1, "unit_price": "49.00"})
    _post("/orders/calculate", {"item_id": 3, "quantity": 5, "unit_price": "3.50"})

    # ── TRAP 3: __root__ model — POST /products/tags ──────────────────
    _post("/products/tags?product_id=1", ["electronics", "sale"])
    _post("/products/tags?product_id=2", ["books", "fiction"])
    _post("/products/tags?product_id=3", ["clothing", "summer", "new-arrival"])

    # ── TRAP 4: each_item validator — POST /reviews/bulk ─────────────
    _post("/reviews/bulk", {
        "reviews": [
            {"product_id": 1, "rating": 5, "comment": "Excellent!"},
            {"product_id": 2, "rating": 4, "comment": "Good value"},
        ]
    })
    _post("/reviews/bulk", {
        "reviews": [
            {"product_id": 3, "rating": 3, "comment": "Average"},
        ]
    })
    _post("/reviews/bulk", {
        "reviews": [
            {"product_id": 1, "rating": 1, "comment": "Terrible"},
            {"product_id": 2, "rating": 2, "comment": "Below expectations"},
            {"product_id": 3, "rating": 5, "comment": "Perfect"},
        ]
    })

    # ── TRAP 4 edge cases — demonstrate systematic validator loss ─────
    _post("/reviews/bulk", {
        "reviews": [{"product_id": 1, "rating": 99, "comment": "high out of range"}]
    })
    _post("/reviews/bulk", {
        "reviews": [{"product_id": 2, "rating": -5, "comment": "negative rating"}]
    })
    _post("/reviews/bulk", {
        "reviews": [{"product_id": 3, "rating": 0, "comment": "zero rating"}]
    })

    print("Seed traffic complete.")


if __name__ == "__main__":
    run()
