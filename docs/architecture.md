# Secure SaaS Accountant Architecture

This document outlines a production-minded architecture for a rules-first SaaS accountant that ingests TD / TD MySpend and other providers, applies deterministic logic for categorization and budgets, and syncs into Notion via MCP-enabled services.

## 1. Layered system overview

### A. Data layer (bank/aggregator to ingestion)
- **Providers:** Use a Canadian-compatible aggregator (e.g., Plaid or Flinks) with read-only scopes for TD/TD MySpend and optional PayPal/other accounts.
- **Ingestion service:**
  - Runs behind an MCP server and polls providers with short-lived access tokens only (no banking credentials stored).
  - Normalizes data to a stable schema (id, date, amount, currency, merchant, source, raw category, metadata).
  - Persists transactions in PostgreSQL with encrypted volumes; tokens are encrypted at rest and rotated.

### B. Logic layer (deterministic accountant brain)
- **Rule engine:** Deterministic rule evaluation (e.g., json-rules-engine or a custom matcher) for category/bucket assignment and budget enforcement.
- **Priority & explainability:** Rules evaluated by priority; every decision records the matching rule for auditability.
- **Budgets/limits:** Per-bucket monthly limits; alerts triggered when thresholds are crossed.
- **LLM fallback (optional):** Local-only model via MCP for uncategorized transactions; receives only merchant text/amount and returns a suggestion with rationale.

### C. Sync layer (Notion + reports)
- **Notion worker:** Upserts processed transactions into Notion databases (master transactions + optional buckets/summary tables).
- **Refresh loop:** After each ingestion run, apply rules, flag alerts, then sync deltas to Notion; maintain idempotency via external_id mapping.
- **Reporting:** Generate monthly rollups (spend per bucket, % of budget used) that Notion formulas/relations can surface in dashboards.

## 2. Tech stack

### Core services
- **Language:** Python for rich SDK support (Plaid/Flinks/Notion) and fast MCP tooling.
- **API framework:** FastAPI with async IO, Pydantic models, and OpenAPI for internal tooling.
- **Storage:** PostgreSQL (encrypted volumes). Tables: accounts, transactions, rules, rule_executions, budgets, sync_state.
- **Background jobs:** Celery or APScheduler for ingestion and Notion sync cadence; cron-friendly for self-hosted use.

### MCP server/tools
Expose deterministic tools to the agent layer:
- `fetch_transactions(account_id, since)`
- `apply_rules(transaction_batch_id)`
- `suggest_category(transaction_id)` (local LLM, optional)
- `sync_to_notion(batch_id)`
- `generate_monthly_report(month, year)`

### Frontend
- Minimal Next.js dashboard for auth, connection status, rule management, and budget settings; all sensitive flows routed to provider widgets (Plaid/Flinks) and never touch your servers directly.

## 3. Security model

### Data minimization & access control
- **Read-only scopes** everywhere; no payment initiation or transfer permissions.
- **No credential storage;** only provider-issued access tokens encrypted at rest with envelope encryption (KMS/Vault).
- **Least privilege** Notion integration token; scoped to specific databases.
- **Strong auth:** OIDC (Auth0/Keycloak) with WebAuthn or TOTP MFA; per-user RBAC for rule editing vs. view-only roles.

### Transport & storage protections
- **TLS 1.2+** with HSTS; Caddy/Nginx reverse proxy for certificate management.
- **Encrypted volumes** for PostgreSQL; application-level token encryption for secrets.
- **Logging/observability:** Structured logs with PII redaction; audit trails for MCP tool invocations and rule changes.

### Isolation & execution safety
- **MCP isolation:** MCP server runs in a restricted container/namespace; tools whitelist outbound hosts (aggregator + Notion only).
- **LLM isolation:** Local-only model with no internet access; receives redacted payloads.
- **Secrets management:** Central store (Vault/Doppler/SM) with short TTL tokens and rotation; no secrets in images or repos.

## 4. Integration flows

### Daily sync (automated)
1. Scheduler triggers MCP tool `fetch_transactions(account_id, since=last_sync)`.
2. Backend pulls new transactions from aggregator using read-only tokens.
3. Apply deterministic rules; record rule matches and over-limit flags.
4. Optional: LLM suggestion for uncategorized items (logged, human-reviewable).
5. MCP triggers `sync_to_notion` to upsert rows in Notion (idempotent by transaction id).
6. Generate/update summary pages for budgets and alerts.

### Rule update flow
1. User edits/creates rules via UI (or MCP command).
2. Rules stored with priority, scope (field + pattern), and target category/bucket.
3. Re-run `apply_rules` on recent transactions; resync impacted rows to Notion.

### Alerting flow
- Budget definitions live in the `budgets` table (bucket, monthly_limit).
- A post-rule check emits alerts when actual > limit or when projected spend exceeds limit.
- Alerts can be surfaced in Notion or sent via email/push; all alert emissions logged.

## 5. MVP implementation path

1. **Repo scaffold**
   - Services: `api/` (FastAPI), `rules/` (engine), `notion_sync/`, `mcp/` (tool wrappers), `infra/` (Docker Compose, TLS termination), `docs/`.
2. **Schema + models**
   - Implement Pydantic models for transactions/rules/budgets; PostgreSQL migrations for core tables and rule_executions.
3. **Provider integration**
   - Plaid/Flinks client with read-only scopes; webhook handler for new transactions; token storage via KMS-wrapped secrets.
4. **Rule engine**
   - Deterministic matcher with priority ordering and audit log of matched rule; add LLM suggestion hook (feature-flagged, local-only).
5. **Notion sync**
   - Idempotent upsert into Transactions DB; maintain mapping between internal txn id and Notion page id; expose `sync_to_notion` MCP tool.
6. **Security hardening**
   - TLS via Caddy, secret injection via Vault/SM, MFA-backed admin UI, outbound allowlist for MCP container, structured logging with redaction.
7. **Deploy modes**
   - Local paranoid mode via Docker Compose (api + db + mcp + reverse proxy).
   - Private cloud mode with encrypted volumes, IP allowlists, and separate secret store.

## 6. Future enhancements
- **Policy-as-code:** Store rules/budgets as signed JSON policies; require review/approval workflow for changes.
- **Anomaly detection:** Add statistical baselines per merchant/bucket; keep LLM suggestions optional and explainable.
- **Multi-tenant SaaS:** Per-tenant DB schemas or row-level security; per-tenant Notion integration tokens; scoped MCP tool access.
- **Offline exports:** Encrypted CSV/Parquet exports for local backups; optional local-only mode without Notion.
