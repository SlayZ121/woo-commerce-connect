# Private WooCommerce Connector for Agent Studio

This project implements a small, private connector for WooCommerce so an agent can read orders and stock without exposing arbitrary admin endpoints. It uses the WooCommerce REST API with API-key-style credentials and includes a mock server for a working local demonstration.

## What it includes

- `connector.py` – a reusable connector class with API-key-style WooCommerce authentication and read-only list/get/search primitives
- `mock_woocommerce_server.py` – a local HTTP server that mimics WooCommerce responses, including a retry-after rate-limit scenario
- `mcp/woocommerce_connector.json` – a simple MCP-like tool specification for agent use
- `docs/agent_capabilities.md` – limitations, safe usage, and agent boundaries

## Setup

No external dependencies are required. Python 3.10+ is sufficient.

1. Open a terminal in this folder.
2. Run the demo:

```bash
python demo.py
```

3. To run the tests:

```bash
python -m unittest discover -s tests -v
```

## Local demo behavior

The demo uses a bundled mock server so the connector can authenticate with the WooCommerce API-key model (consumer key + consumer secret via Basic Auth) and read:

- order list
- single order details
- product search
- inventory list

The credentials are deliberately demo-only values:

- consumer key: `ck_demo_key`
- consumer secret: `cs_demo_secret`

Do not use these in production.

## Assumptions and limitations

- This is a private connector pattern for a WooCommerce store, not a general public API.
- It is designed for read-only access to orders and product inventory.
- It assumes the store exposes the standard WooCommerce REST endpoints on the configured base URL.
- It does not implement write/update actions or sensitive customer-account tools.
- In production, the long-term fix is to expose a controlled, documented API or use a proper middleware layer with OAuth / service principal / scoped credentials and rate-limit handling.

## What the agent can do

- read order status and basic billing information
- fetch order detail by ID
- search products by name or SKU
- read stock and availability data

## What the agent cannot do

- modify orders or inventory
- access payment details beyond what the configured API allows
- access unrelated admin routes or private customer files
- bypass access controls or use customer data not explicitly permitted
