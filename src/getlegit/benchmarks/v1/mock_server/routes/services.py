"""Route handlers for /api/service-a, /api/service-b, /api/service-c endpoints."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


def handle_service(service_name: str, scenario: str = "default") -> tuple[int, dict]:
    """GET /api/service-{a,b,c} - return data based on the service and scenario.

    The scenario is determined by the X-Scenario header (defaults to 'default').
    """
    data = load_fixture("services.json")
    service_data = data.get(service_name)
    if service_data is None:
        return 404, {"error": f"Unknown service: {service_name}"}

    scenario_data = service_data.get(scenario, service_data.get("default"))
    if scenario_data is None:
        return 404, {"error": f"Unknown scenario '{scenario}' for {service_name}"}

    return 200, scenario_data
