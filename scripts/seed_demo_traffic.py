"""Deterministic seed script — generates ~40 HTTP interactions hitting every endpoint 3x+.

Run against the Pydantic v1 app on localhost:8001 before capture_baseline.
Usage: python scripts/seed_demo_traffic.py
"""

import httpx

BASE = "http://localhost:8001"


def _post(client: httpx.Client, path: str, json: dict) -> httpx.Response:
    return client.post(path, json=json)


def run() -> None:
    with httpx.Client(base_url=BASE, timeout=10.0) as c:

        # Reset to deterministic initial state before capturing
        c.post("/admin/reset")

        # ── Control: health ───────────────────────────────────────────────
        for _ in range(3):
            c.get("/health")

        # ── Control: list users ───────────────────────────────────────────
        for _ in range(3):
            c.get("/users")

        # ── Control: create users ─────────────────────────────────────────
        c.post("/users", json={"name": "Dave", "email": "dave@example.com"})
        c.post("/users", json={"name": "Eve", "email": "eve@example.com"})
        c.post("/users", json={"name": "Frank", "email": "frank@example.com"})

        # ── Control: update user ──────────────────────────────────────────
        c.put("/users/1", json={"name": "Alice Updated"})
        c.put("/users/2", json={"email": "bob2@example.com"})
        c.put("/users/3", json={"name": "Carol Updated", "email": "carol2@example.com"})

        # ── Control: user orders ──────────────────────────────────────────
        for user_id in [1, 2, 1]:
            c.get(f"/users/{user_id}/orders")

        # ── Control: delete user ──────────────────────────────────────────
        # create temp users to delete
        r1 = c.post("/users", json={"name": "Temp1", "email": "t1@example.com"})
        r2 = c.post("/users", json={"name": "Temp2", "email": "t2@example.com"})
        r3 = c.post("/users", json={"name": "Temp3", "email": "t3@example.com"})
        for r in [r1, r2, r3]:
            if r.status_code == 201:
                uid = r.json()["id"]
                c.delete(f"/users/{uid}")

        # ── TRAP 1: Enum serialization — GET /users/{id} ──────────────────
        for user_id in [1, 2, 3]:
            c.get(f"/users/{user_id}")

        # ── TRAP 2: Decimal serialization — POST /orders/calculate ────────
        _post(c, "/orders/calculate", {"item_id": 1, "quantity": 2, "unit_price": "9.99"})
        _post(c, "/orders/calculate", {"item_id": 2, "quantity": 1, "unit_price": "49.00"})
        _post(c, "/orders/calculate", {"item_id": 3, "quantity": 5, "unit_price": "3.50"})

        # ── TRAP 3: __root__ model — POST /products/tags ──────────────────
        _post(c, "/products/tags?product_id=1", ["electronics", "sale"])
        _post(c, "/products/tags?product_id=2", ["books", "fiction"])
        _post(c, "/products/tags?product_id=3", ["clothing", "summer", "new-arrival"])

        # ── TRAP 4: each_item validator — POST /reviews/bulk ─────────────
        _post(c, "/reviews/bulk", {
            "reviews": [
                {"product_id": 1, "rating": 5, "comment": "Excellent!"},
                {"product_id": 2, "rating": 4, "comment": "Good value"},
            ]
        })
        _post(c, "/reviews/bulk", {
            "reviews": [
                {"product_id": 3, "rating": 3, "comment": "Average"},
            ]
        })
        _post(c, "/reviews/bulk", {
            "reviews": [
                {"product_id": 1, "rating": 1, "comment": "Terrible"},
                {"product_id": 2, "rating": 2, "comment": "Below expectations"},
                {"product_id": 3, "rating": 5, "comment": "Perfect"},
            ]
        })

    print("Seed traffic complete.")


if __name__ == "__main__":
    run()
