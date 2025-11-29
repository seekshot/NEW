# Security and Infrastructure

## Security principles
- Read-only access to financial data; no money-movement capabilities.
- No credential storage—only aggregator-issued access tokens.
- Least-privilege tokens for both aggregator and Notion integrations.
- Encryption in transit (TLS 1.2+) and at rest for disks and sensitive columns.
- Minimal PII retention; store only what is required for categorization and auditing.
- Auditable rule execution and MCP activity with tamper-evident logs.

## Data classification
- **Aggregator/Access tokens** — Sensitivity: High; Storage: PostgreSQL encrypted columns; Protection: envelope encryption via KMS/Vault keys, strict RBAC.
- **Transaction metadata (dates, amounts, merchants)** — Sensitivity: Medium; Storage: PostgreSQL tables; Protection: encrypted volume, row-level access controls where applicable.
- **User configuration (rules, budgets, alerts)** — Sensitivity: Medium; Storage: PostgreSQL; Protection: encrypted volume, change audit trail.
- **Notion integration token** — Sensitivity: High; Storage: secrets manager or encrypted column; Protection: least-privilege scope to required databases only.

## Transport security
- All external traffic served over HTTPS with TLS 1.2+.
- Reverse proxy (Caddy or Nginx) terminates TLS and enforces HSTS in production.
- Strong cipher suites and redirect HTTP → HTTPS.

## Storage security
- **PostgreSQL:** Encrypted disk/volume; application-level encryption for sensitive columns using envelope encryption (e.g., KMS/Vault-managed DEKs wrapped by KEKs).
- **Backups:** Encrypted at rest, short retention, access limited to operators; restore procedures tested regularly.

## Secrets management
- **Local paranoid mode:** Secrets loaded from `.env` or a local secret store; never committed to git.
- **Private cloud mode:** Secrets injected from Vault or a cloud Secret Manager; no secrets baked into images.
- **Rotation:** Aggregator tokens rotated via provider APIs; Notion tokens regenerated when compromised; configurable TTLs for all stored secrets.

## LLM and MCP isolation
- MCP server runs in its own container/namespace with a strict outbound allowlist (aggregator API and Notion only).
- Local LLM container has no outbound internet access; receives redacted payloads without account numbers or credentials.
- Tool execution is audited; payloads are bounded and validated to prevent data exfiltration.

## Deployment modes

### Local paranoid mode
- Docker Compose stack: `api` (FastAPI), `db` (PostgreSQL), `mcp` (tools server), `reverse-proxy` (Caddy/Nginx for TLS).
- All services bind to localhost by default; optional LAN-only exposure with firewall rules.
- Use a local CA or mkcert for HTTPS during development; validate certificates in clients.

### Private cloud mode
- Single-tenant deployment per user/tenant with isolated databases and Notion tokens.
- Encrypted volumes, host-level firewall rules, and IP allowlists for the admin/UI surface.
- Managed Postgres (e.g., RDS) with encryption at rest and in transit; backups encrypted and access-controlled.
- CI/CD with image scanning, minimal base images, non-root containers, and signed artifacts where supported.

## Logging & observability
- Log service health, errors, rule application events, MCP tool invocations, and sync outcomes with correlation IDs per request/tool call.
- Do not log full tokens, PANs, or sensitive PII; redact merchants/descriptions only when required for privacy contracts.
- Emit metrics for ingestion latency, rule throughput, sync success rates, and alert volume; use alerts on anomalies.

