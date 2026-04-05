"""Route handlers for /api/orders endpoints."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

# In-memory store for created orders (keyed by id)
_created_orders: dict[int, dict] = {}
_next_id = 201


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


def handle_get_orders() -> tuple[int, dict]:
    """GET /api/orders - return all orders."""
    data = load_fixture("orders.json")
    return 200, data


def handle_create_order(body: dict) -> tuple[int, dict]:
    """POST /api/orders - create a new order."""
    global _next_id
    order_id = _next_id
    _next_id += 1
    order = {**body, "id": order_id}
    _created_orders[order_id] = order
    return 201, {
        "id": order_id,
        "status": "created",
        "message": "Order created successfully",
    }


def handle_get_order(order_id: int) -> tuple[int, dict]:
    """GET /api/orders/{id} - return a specific order."""
    if order_id in _created_orders:
        return 200, _created_orders[order_id]
    # Check fixtures
    data = load_fixture("orders.json")
    for order in data["orders"]:
        if order["id"] == order_id:
            return 200, order
    return 404, {"error": "Order not found", "id": order_id}


def handle_update_order(order_id: int, body: dict) -> tuple[int, dict]:
    """PUT /api/orders/{id} - update an order."""
    if order_id in _created_orders:
        _created_orders[order_id].update(body)
        return 200, {
            "id": order_id,
            "status": "updated",
            "message": "Order updated successfully",
        }
    return 404, {"error": "Order not found", "id": order_id}


def handle_delete_order(order_id: int) -> tuple[int, dict]:
    """DELETE /api/orders/{id} - delete an order."""
    if order_id in _created_orders:
        del _created_orders[order_id]
        return 204, {}
    return 404, {"error": "Order not found", "id": order_id}


def reset():
    """Reset in-memory state (useful for testing)."""
    global _next_id
    _created_orders.clear()
    _next_id = 201
