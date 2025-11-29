# Getting Started

## Prerequisites
- Docker and Docker Compose.
- Python 3.11+ (for local dev without Docker).
- A Notion integration and database set up for transactions (see Notion API docs for creating an integration and database ID).
- Aggregator sandbox credentials (e.g., Plaid/Flinks) with read-only scopes.

## Quickstart (Docker)
1. Clone the repo.
2. Copy `.env.example` to `.env` and populate aggregator keys, Notion token, and an optional database URL.
3. Run `docker compose up --build`.
4. Visit `https://localhost` (or the configured port) to verify health endpoints.
5. Run initial migrations if applicable, for example: `docker compose exec api alembic upgrade head`.

## Quickstart (bare metal / dev mode)
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start PostgreSQL (local instance or container) and set `DATABASE_URL`.
4. Set required env vars (aggregator keys, Notion token, secret key, etc.).
5. Run the API: `uvicorn app.main:app --reload`.
6. This mode is for local development only; use Docker for anything exposed beyond localhost.

## Connecting a bank sandbox
1. Use your aggregator’s sandbox link/token flow to simulate a TD/PayPal connection.
2. Call `POST /accounts/connect/callback` with the provided `public_token`/authorization code or complete the UI flow.
3. Confirm the account is registered with `GET /accounts`.

## First ingestion & Notion sync
1. Trigger ingestion: `POST /ingest/run` with your `account_id` (optionally include `since`).
2. Apply rules via MCP (`apply_rules`) or the equivalent API endpoint.
3. Sync to Notion: `POST /notion/sync` for the same account and date range.
4. See `docs/api-usage.md` and `docs/mcp-tools.md` for payload details.

## Where to go next
- Tweak rules and budgets to match your spend model.
- Harden the deployment; see `docs/security-and-infra.md`.
- Read `docs/architecture.md` for the full design context.

