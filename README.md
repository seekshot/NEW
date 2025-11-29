# Secure SaaS Accountant MVP

Minimal FastAPI + SQLite implementation to ingest mock transactions, apply deterministic rules, and produce a monthly bucket report. Notion sync is currently stubbed.

Includes a lightweight HTML demo at `/demo` for quick screenshots and portfolio walkthroughs.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000 (interactive docs at `/docs`).

## Basic flow

1. **Create an account**
   ```bash
   curl -X POST http://127.0.0.1:8000/accounts \
     -H "Content-Type: application/json" \
     -d '{"name":"TD Chequing","provider":"MOCK","institution":"TD"}'
   ```
2. **Ingest mock transactions** for that account id:
   ```bash
   curl -X POST http://127.0.0.1:8000/ingest/mock \
     -H "Content-Type: application/json" \
     -d '{"account_id":1}'
   ```
3. **Create a rule** (e.g., classify UBER as Transport):
   ```bash
   curl -X POST http://127.0.0.1:8000/rules \
     -H "Content-Type: application/json" \
      -d '{"pattern":"UBER","field":"merchant","category":"Transport","bucket":"Transport","priority":10,"enabled":true}'
   ```
4. **Apply rules**:
   ```bash
   curl -X POST http://127.0.0.1:8000/apply-rules \
     -H "Content-Type: application/json" \
     -d '{"account_id":1}'
   ```
5. **Generate monthly report**:
   ```bash
   curl "http://127.0.0.1:8000/reports/monthly?year=2025&month=11"
   ```
6. **Open the demo UI**:
   Navigate to http://127.0.0.1:8000/demo to view bucket summaries and recent transactions.

## Notes
- SQLite database file: `saas_accountant.db` in the repo root.
- Sample transactions live in `sample_data/transactions_td_demo.json`.
- Notion sync endpoint is stubbed and returns counters only.
- Demo UI assets live in `templates/` and `static/`.
- For background and design rationale, see docs/*.md.
