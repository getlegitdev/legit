"""Route handlers for /api/products endpoints."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


def handle_get_products() -> tuple[int, dict]:
    """GET /api/products - return all products."""
    data = load_fixture("products.json")
    return 200, data
