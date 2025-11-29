# API Usage

## Overview
This FastAPI service ingests read-only banking data, applies deterministic categorization and budgeting rules, triggers Notion syncs, and exposes reporting endpoints for integrators. Authentication is expected via bearer tokens or session-based auth; the exact identity provider is implementation-defined.

## Authentication
Use standard bearer tokens in the `Authorization` header (for example, `Authorization: Bearer <token>`). In production, wire this to an OIDC provider (Auth0, Keycloak, etc.). This document is auth-mechanism-agnostic; every request must include valid credentials or will be rejected.

## Core endpoints

### Accounts & Aggregator Integration
- **POST `/accounts/connect/callback`**
  - Purpose: Handle aggregator callback to exchange a `public_token`/`authorization_code` for an access token and register the account.
  - Request body example:
    ```json
    {
      "public_token": "public-sandbox-abc",
      "institution": "TD",
      "metadata": {"account_mask": "***1234", "source": "plaid"}
    }
    ```
  - Response example:
    ```json
    {
      "account_id": 42,
      "institution": "TD",
      "account_mask": "***1234"
    }
    ```

- **GET `/accounts`**
  - Purpose: List connected accounts (masked, read-only view).
  - Response example:
    ```json
    [
      {"account_id": 42, "institution": "TD", "account_mask": "***1234", "last_sync": "2025-01-05T12:00:00Z"},
      {"account_id": 7, "institution": "PayPal", "account_mask": "***7788", "last_sync": "2025-01-04T23:10:00Z"}
    ]
    ```

### Transactions
- **GET `/transactions`**
  - Purpose: List normalized transactions.
  - Query params: `account_id` (required), `from` (ISO8601), `to` (ISO8601), `page`, `page_size`.
  - Response example:
    ```json
    {
      "items": [
        {
          "id": "txn_123",
          "date": "2025-01-02",
          "amount": -23.45,
          "currency": "CAD",
          "merchant": "UBER *TRIP",
          "category": "Transport",
          "bucket": "Travel",
          "source": "TD_CHEQUING"
        }
      ],
      "page": 1,
      "page_size": 50,
      "total": 1
    }
    ```

- **POST `/ingest/run`**
  - Purpose: Manually trigger ingestion for accounts.
  - Request body example:
    ```json
    {
      "account_ids": [42, 7],
      "since": "2025-01-01T00:00:00Z"
    }
    ```
  - Response example:
    ```json
    {"fetched": 120, "inserted": 118, "updated": 2}
    ```

### Rules
- **GET `/rules`** — List rules.
- **POST `/rules`** — Create a rule.
- **PUT `/rules/{id}`** — Update a rule.
- **DELETE `/rules/{id}`** — Delete a rule.

Rule payload fields: `pattern`, `field` (e.g., `merchant`), `category`, `bucket`, `priority`, `enabled`.

Example request to create a transport rule for Uber:
```json
{
  "pattern": "UBER",
  "field": "merchant",
  "category": "Transport",
  "bucket": "Travel",
  "priority": 90,
  "enabled": true
}
```

### Budgets
- **GET `/budgets`** — List budgets.
- **POST `/budgets`** — Create or update a budget.

Budget fields: `bucket`, `monthly_limit`, `currency`, `alert_threshold` (0–1).

Example monthly Food budget:
```json
{
  "bucket": "Food",
  "monthly_limit": 600.00,
  "currency": "CAD",
  "alert_threshold": 0.8
}
```

### Notion Sync
- **POST `/notion/sync`**
  - Purpose: Sync processed transactions to Notion.
  - Request body example:
    ```json
    {
      "account_id": 42,
      "from": "2025-01-01",
      "to": "2025-01-05"
    }
    ```
  - Response example:
    ```json
    {"created": 50, "updated": 12, "failed_ids": []}
    ```

### Reports
- **GET `/reports/monthly`**
  - Purpose: Retrieve monthly spend vs. budget per bucket.
  - Query params: `year` (required), `month` (required), `account_id` (optional).
  - Response example:
    ```json
    {
      "year": 2025,
      "month": 1,
      "buckets": [
        {"bucket": "Food", "spent": 420.10, "limit": 600.00, "utilization": 0.70, "status": "under"},
        {"bucket": "Transport", "spent": 215.00, "limit": 200.00, "utilization": 1.08, "status": "over"}
      ]
    }
    ```

## Error model
The API uses standard HTTP status codes. Errors return JSON with machine-friendly codes and human-readable messages. Example:

```json
{
  "error_code": "INVALID_INPUT",
  "message": "`account_id` is required",
  "details": {"field": "account_id"}
}
```

