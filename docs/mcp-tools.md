# MCP Tools

## Overview
The MCP tool surface wraps the backend API in a controlled, deterministic interface for automation and LLM agents. Tools are purpose-scoped, side-effect-limited, and never expose raw banking credentials; all sensitive operations stay within the backend’s policy boundaries.

## Tool list

### `fetch_transactions`
- **Purpose:** Retrieve normalized transactions for an account.
- **Inputs:** `account_id` (required), `since` (ISO8601, optional).
- **Outputs:** List of transactions `{id, date, amount, currency, merchant, category, bucket, source}`.
- **Side effects:** None (read-only).

### `apply_rules`
- **Purpose:** Apply deterministic rules to transactions.
- **Inputs:** Either `transaction_ids` (array) or `account_id` + `since` (ISO8601).
- **Outputs:** Transactions with applied `category`, `bucket`, and `matched_rule_id`.
- **Side effects:** Persists rule decisions to stored transactions and appends an entry to `rule_executions` audit log.

### `suggest_category`
- **Purpose:** Provide a best-effort category suggestion using a local-only LLM for uncategorized transactions.
- **Inputs:** `transaction_id` **or** an inline transaction object `{date, amount, merchant, description}`.
- **Outputs:** Suggested `category`, optional `bucket`, and a short `rationale` string.
- **Side effects:** None; suggestions are advisory. Runs only on a local model with no outbound network access.

### `sync_to_notion`
- **Purpose:** Upsert processed transactions into Notion databases.
- **Inputs:** `account_id` (required), `from` (optional), `to` (optional).
- **Outputs:** `{created, updated, failed_ids}` counters.
- **Side effects:** Writes/updates Notion pages via the Notion API.

### `generate_monthly_report`
- **Purpose:** Produce a structured monthly spend vs. budget report.
- **Inputs:** `year`, `month`, optional `account_id`.
- **Outputs:** Per-bucket totals with `limit`, `utilization`, and `status` (over/under).
- **Side effects:** May optionally create/update a Notion “Monthly Summary” page.

### `list_alerts`
- **Purpose:** Retrieve budget/threshold alerts.
- **Inputs:** `since` (optional, ISO8601).
- **Outputs:** Alert list `{id, bucket, actual_spend, limit, created_at, resolved}`.
- **Side effects:** None (read-only).

## Tool usage examples

### Example 1: Daily sync flow
```json
{
  "steps": [
    {"tool": "fetch_transactions", "params": {"account_id": 42, "since": "2025-01-04T00:00:00Z"}},
    {"tool": "apply_rules", "params": {"account_id": 42, "since": "2025-01-04T00:00:00Z"}},
    {"tool": "sync_to_notion", "params": {"account_id": 42, "from": "2025-01-04", "to": "2025-01-05"}},
    {"tool": "generate_monthly_report", "params": {"year": 2025, "month": 1, "account_id": 42}}
  ]
}
```

### Example 2: Re-run rules after a rule update
```json
{
  "steps": [
    {"tool": "apply_rules", "params": {"account_id": 42, "since": "2025-01-01T00:00:00Z"}},
    {"tool": "sync_to_notion", "params": {"account_id": 42, "from": "2025-01-01"}}
  ]
}
```

