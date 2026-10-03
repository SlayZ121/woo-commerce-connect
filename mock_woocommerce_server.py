from __future__ import annotations

import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ORDERS = [
    {
        "id": 101,
        "number": "101",
        "status": "pending",
        "currency": "USD",
        "total": "49.00",
        "billing": {"first_name": "Ava", "last_name": "Nguyen", "email": "ava@example.com"},
        "line_items": [{"product_id": 10, "name": "Espresso Beans", "quantity": 1, "total": "19.00"}],
    },
    {
        "id": 102,
        "number": "102",
        "status": "processing",
        "currency": "USD",
        "total": "89.00",
        "billing": {"first_name": "Sam", "last_name": "Martin", "email": "sam@example.com"},
        "line_items": [{"product_id": 11, "name": "Pour Over Kit", "quantity": 1, "total": "79.00"}],
    },
]

RATE_LIMIT_CALLS = {"orders": 0}

PRODUCTS = [
    {"id": 10, "name": "Espresso Beans", "sku": "ESP-01", "stock_quantity": 42, "stock_status": "instock"},
    {"id": 11, "name": "Pour Over Kit", "sku": "POUR-02", "stock_quantity": 17, "stock_status": "instock"},
    {"id": 12, "name": "Burr Grinder", "sku": "GRIND-03", "stock_quantity": 9, "stock_status": "instock"},
    {"id": 13, "name": "Tea Filter Set", "sku": "TEA-04", "stock_quantity": 0, "stock_status": "outofstock"},
]


def _check_auth(headers):
    auth = headers.get("Authorization")
    if not auth or not auth.startswith("Basic "):
        return False
    encoded = auth.split(" ", 1)[1]
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return False
    username, password = decoded.split(":", 1)
    return username == "ck_demo_key" and password == "cs_demo_secret"


class DemoWooHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not _check_auth(self.headers):
            self._send_json({"code": "woocommerce_rest_cannot_authenticate", "message": "Unauthorized"}, status=401)
            return

        url_path = self.path.split("?", 1)[0]

        if url_path == "/wp-json/wc/v3/orders/rate-limit-check":
            RATE_LIMIT_CALLS["orders"] += 1
            if RATE_LIMIT_CALLS["orders"] == 1:
                self.send_response(429)
                self.send_header("Retry-After", "0.1")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"code": "rate_limit_exceeded", "message": "Too many requests"}')
                return
            self._send_json([{"id": 999, "status": "pending", "billing": {"email": "retry@example.com"}}])
            return

        if url_path.startswith("/wp-json/wc/v3/system_status"):
            self._send_json({"status": "ok", "environment": "demo"})
            return

        if url_path.startswith("/wp-json/wc/v3/orders"):
            if url_path == "/wp-json/wc/v3/orders":
                self._send_json(ORDERS[:2])
                return
            order_id = url_path.rsplit("/", 1)[1]
            for order in ORDERS:
                if str(order["id"]) == order_id:
                    self._send_json(order)
                    return
            self._send_json({"code": "not_found", "message": "Order not found"}, status=404)
            return

        if url_path.startswith("/wp-json/wc/v3/products"):
            query = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = {}
            if query:
                for item in query.split("&"):
                    if "=" in item:
                        k, v = item.split("=", 1)
                        params[k] = v
            if params.get("search"):
                term = params["search"].lower()
                matches = [p for p in PRODUCTS if term in p["name"].lower() or term in p["sku"].lower()]
                self._send_json(matches[:5])
                return
            if params.get("stock_status") == "instock":
                self._send_json([p for p in PRODUCTS if p["stock_status"] == "instock"])
                return
            self._send_json(PRODUCTS)
            return

        self._send_json({"code": "not_found", "message": "Unknown route"}, status=404)

    def log_message(self, *args, **kwargs):
        return


def start_test_server(host: str = "127.0.0.1", port: int = 8765):
    server = ThreadingHTTPServer((host, port), DemoWooHandler)
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":
    server = start_test_server()
    print("WooCommerce demo server running on http://127.0.0.1:8765")
    input("Press Enter to stop the server...\n")
    server.shutdown()
    server.server_close()
