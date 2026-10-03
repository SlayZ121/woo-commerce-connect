from __future__ import annotations

import base64
import json
import time
from urllib import error, request
from urllib.parse import urlencode


class WooCommerceConnector:
    """Thin connector for the WooCommerce REST API.

    This class intentionally exposes a minimal, agent-friendly set of primitives:
    - authenticate()
    - list_orders()
    - get_order()
    - search_products()
    - list_inventory()
    """

    def __init__(self, base_url: str, consumer_key: str, consumer_secret: str):
        self.base_url = base_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def _build_url(self, path: str, params: dict | None = None) -> str:
        url = f"{self.base_url}{path}"
        if params:
            query = urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"
        return url

    def _request(self, path: str, method: str = "GET", params: dict | None = None, payload: dict | None = None, retries: int = 0):
        url = self._build_url(path, params)
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if payload is not None:
            req.add_header("Content-Type", "application/json")
        credentials = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode("utf-8")).decode("ascii")
        req.add_header("Authorization", f"Basic {credentials}")

        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except error.HTTPError as exc:
            response_text = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 and retries < 2:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                delay = float(retry_after) if retry_after is not None else 1.0
                time.sleep(max(delay, 0.1))
                return self._request(path, method, params, payload, retries + 1)
            raise RuntimeError(f"WooCommerce API call failed: {exc.code} {response_text}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Could not reach WooCommerce API at {url}: {exc}") from exc

    def authenticate(self) -> bool:
        try:
            response = self._request("/wp-json/wc/v3/system_status")
            return isinstance(response, dict) and response.get("status") == "ok"
        except RuntimeError:
            return False

    def list_orders(self, per_page: int = 10, status: str | None = None):
        params = {"per_page": per_page, "status": status}
        return self._request("/wp-json/wc/v3/orders", params=params)

    def get_order(self, order_id: int):
        return self._request(f"/wp-json/wc/v3/orders/{order_id}")

    def search_products(self, query: str, per_page: int = 10):
        params = {"search": query, "per_page": per_page}
        return self._request("/wp-json/wc/v3/products", params=params)

    def list_inventory(self, per_page: int = 10):
        params = {"per_page": per_page, "stock_status": "instock"}
        products = self._request("/wp-json/wc/v3/products", params=params)
        return [
            {
                "id": product.get("id"),
                "name": product.get("name"),
                "sku": product.get("sku"),
                "stock_quantity": product.get("stock_quantity"),
                "stock_status": product.get("stock_status"),
            }
            for product in products
        ]

    def tool_spec(self):
        return {
            "name": "woocommerce_private_connector",
            "version": "1.0.0",
            "description": "Read WooCommerce orders and product inventory for an agent.",
            "tools": [
                {
                    "name": "woo_list_orders",
                    "description": "List recent WooCommerce orders.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "per_page": {"type": "integer", "default": 10},
                            "status": {"type": "string", "enum": ["pending", "processing", "completed", "cancelled", "refunded", "on-hold", "failed"]},
                        },
                    },
                },
                {
                    "name": "woo_get_order",
                    "description": "Get a single WooCommerce order by ID.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"order_id": {"type": "integer", "minimum": 1}},
                        "required": ["order_id"],
                    },
                },
                {
                    "name": "woo_search_products",
                    "description": "Search WooCommerce products by name or SKU.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "per_page": {"type": "integer", "default": 10},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "woo_list_inventory",
                    "description": "List current in-stock inventory items.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"per_page": {"type": "integer", "default": 10}},
                    },
                },
            ],
        }


if __name__ == "__main__":
    conn = WooCommerceConnector(
        base_url="http://127.0.0.1:8765",
        consumer_key="ck_demo_key",
        consumer_secret="cs_demo_secret",
    )
    print(conn.authenticate())
    print(conn.list_orders(per_page=2))
