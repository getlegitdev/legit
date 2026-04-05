"""Route handlers for /api/error-endpoint (error recovery testing)."""

# Track call counts per client to simulate error-then-success behavior.
# Key: scenario name, Value: number of calls received.
_call_counts: dict[str, int] = {}

# Map scenario names to error codes for the first call.
_SCENARIO_ERRORS = {
    "default": (500, "Internal Server Error"),
    "service-unavailable": (503, "Service Unavailable"),
    "rate-limited": (429, "Too Many Requests"),
}

_SUCCESS_RESPONSE = {
    "status": "ok",
    "message": "Service recovered successfully",
    "data": {"recovered": True, "timestamp": "2026-04-01T12:00:00Z"},
}


def handle_error_endpoint(scenario: str = "default") -> tuple[int, dict]:
    """GET /api/error-endpoint - returns error on first call, success on retry.

    The scenario is determined by the X-Scenario header:
    - default (or absent): 500 on first call
    - service-unavailable: 503 on first call
    - rate-limited: 429 on first call

    All scenarios return 200 on subsequent calls.
    """
    _call_counts[scenario] = _call_counts.get(scenario, 0) + 1

    if _call_counts[scenario] <= 1:
        error_code, error_msg = _SCENARIO_ERRORS.get(
            scenario, _SCENARIO_ERRORS["default"]
        )
        return error_code, {"error": error_msg}

    return 200, _SUCCESS_RESPONSE


def reset():
    """Reset call counts (useful for testing)."""
    _call_counts.clear()
