"""Route handlers for /api/users endpoints."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


def handle_get_users() -> tuple[int, dict]:
    """GET /api/users - return all users."""
    data = load_fixture("users.json")
    return 200, data


def handle_get_user_orders(user_id: str) -> tuple[int, dict]:
    """GET /api/users/{id}/orders - return orders for a specific user."""
    data = load_fixture("user_orders.json")
    if user_id in data:
        return 200, data[user_id]
    return 404, {"error": "User not found", "user_id": user_id}
