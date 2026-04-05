"""Mock HTTP server for Legit benchmark Operate tasks.

Uses Python's built-in http.server module (no external dependencies).
Listens on localhost:9999 and serves the endpoints needed by tasks O1-O6.

Endpoints:
  GET  /api/users                     - User list (O1)
  GET  /api/products                  - Product list (O1)
  GET  /api/orders                    - Order list (O1)
  POST /api/orders                    - Create order (O2, O3)
  GET  /api/orders/{id}               - Read order (O3)
  PUT  /api/orders/{id}               - Update order (O3)
  DELETE /api/orders/{id}             - Delete order (O3)
  GET  /api/users/{id}/orders         - User's orders (O2)
  GET  /api/error-endpoint            - Error recovery (O4)
  GET  /api/service-a                 - Multi-service A (O5)
  GET  /api/service-b                 - Multi-service B (O5)
  GET  /api/service-c                 - Multi-service C (O5)
  POST /api/workflow/start            - Start workflow (O6)
  GET  /api/workflow/{id}/status      - Workflow status (O6)

Usage:
  python server.py [--port PORT]
"""

from __future__ import annotations

import json
import re
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

# Ensure the package is importable when run directly.
sys.path.insert(0, str(__file__).rsplit("/mock_server", 1)[0])

from mock_server.routes import users, products, orders, errors, services, workflows


class MockRequestHandler(BaseHTTPRequestHandler):
    """Dispatches requests to the appropriate route handler."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _send_json(self, status_code: int, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if body and status_code != 204:
            self.wfile.write(body)

    def _send_no_content(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _not_found(self) -> None:
        self._send_json(404, {"error": "Not found", "path": self.path})

    def _method_not_allowed(self) -> None:
        self._send_json(405, {"error": "Method not allowed"})

    def _get_scenario(self) -> str:
        return self.headers.get("X-Scenario", "default")

    # ------------------------------------------------------------------
    # Route matching helpers
    # ------------------------------------------------------------------

    # Compiled patterns for parameterised routes.
    _RE_USER_ORDERS = re.compile(r"^/api/users/(\d+)/orders$")
    _RE_ORDER_ID = re.compile(r"^/api/orders/(\d+)$")
    _RE_SERVICE = re.compile(r"^/api/service-(a|b|c)$")
    _RE_WORKFLOW_STATUS = re.compile(r"^/api/workflow/([^/]+)/status$")

    # ------------------------------------------------------------------
    # HTTP method handlers
    # ------------------------------------------------------------------

    def do_OPTIONS(self) -> None:  # noqa: N802 – required name
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, X-Scenario")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]  # strip query string

        # Static routes
        if path == "/api/users":
            status, data = users.handle_get_users()
            return self._send_json(status, data)

        if path == "/api/products":
            status, data = products.handle_get_products()
            return self._send_json(status, data)

        if path == "/api/orders":
            status, data = orders.handle_get_orders()
            return self._send_json(status, data)

        if path == "/api/error-endpoint":
            scenario = self._get_scenario()
            status, data = errors.handle_error_endpoint(scenario)
            return self._send_json(status, data)

        # Parameterised routes
        m = self._RE_USER_ORDERS.match(path)
        if m:
            status, data = users.handle_get_user_orders(m.group(1))
            return self._send_json(status, data)

        m = self._RE_ORDER_ID.match(path)
        if m:
            status, data = orders.handle_get_order(int(m.group(1)))
            return self._send_json(status, data)

        m = self._RE_SERVICE.match(path)
        if m:
            service_name = f"service-{m.group(1)}"
            scenario = self._get_scenario()
            status, data = services.handle_service(service_name, scenario)
            return self._send_json(status, data)

        m = self._RE_WORKFLOW_STATUS.match(path)
        if m:
            status, data = workflows.handle_get_workflow_status(m.group(1))
            return self._send_json(status, data)

        self._not_found()

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        body = self._read_body()

        if path == "/api/orders":
            status, data = orders.handle_create_order(body)
            return self._send_json(status, data)

        if path == "/api/workflow/start":
            status, data = workflows.handle_start_workflow(body)
            return self._send_json(status, data)

        self._not_found()

    def do_PUT(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        body = self._read_body()

        m = self._RE_ORDER_ID.match(path)
        if m:
            status, data = orders.handle_update_order(int(m.group(1)), body)
            return self._send_json(status, data)

        self._not_found()

    def do_DELETE(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]

        m = self._RE_ORDER_ID.match(path)
        if m:
            status, data = orders.handle_delete_order(int(m.group(1)))
            if status == 204:
                return self._send_no_content()
            return self._send_json(status, data)

        self._not_found()

    # Suppress default logging for cleaner output.
    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"[mock-server] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}\n")


# ------------------------------------------------------------------
# Server lifecycle
# ------------------------------------------------------------------


def create_server(port: int = 9999) -> HTTPServer:
    """Create and return the mock HTTP server (does not start serving)."""
    server = HTTPServer(("localhost", port), MockRequestHandler)
    return server


def run(port: int = 9999) -> None:
    """Start the mock server and block until interrupted."""
    server = create_server(port)
    print(f"Mock server listening on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock server.")
        server.server_close()


def reset_state() -> None:
    """Reset all in-memory state across route handlers."""
    orders.reset()
    errors.reset()
    workflows.reset()


if __name__ == "__main__":
    port = 9999
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    run(port)
