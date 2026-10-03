# Agent capabilities and constraints

This connector is intended for a narrow, read-only workflow in an Agent Studio environment.

It uses the WooCommerce API-key authentication pattern: a consumer key and consumer secret are sent over HTTP Basic Auth to the store's REST API. This is not OAuth, but it is the standard vendor-provided credential flow for WooCommerce.

## Allowed behavior

The agent may:

- list recent WooCommerce orders
- read a single order by ID
- search products by SKU or name
- inspect stock quantity and stock status

## Rate-limit handling

The connector automatically retries on HTTP 429 responses and honors the Retry-After header when available. If the limit is exceeded repeatedly, it surfaces a clear error instead of retrying forever.

## Disallowed behavior

The agent must not:

- create, modify, or refund orders
- update inventory counts without explicit approval
- access unrelated admin endpoints or customer account data
- bypass authentication, rate limits, or store access policies

## Safe long-term design

For production, the recommended approach is to add a proper service layer or gateway in front of WooCommerce that:

- enforces least-privilege credentials
- exposes only approved read primitives
- logs all actions and data access
- adds retries and throttling for rate-limit handling
- stores secrets in a secret manager instead of embedding them in code
