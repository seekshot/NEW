import datetime as dt
import json
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import crud
from .db import Base, engine, get_db
from .models import Transaction
from .schemas import (
    AccountCreate,
    AccountRead,
    ApplyRulesRequest,
    BudgetCreate,
    BudgetRead,
    IngestMockRequest,
    MonthlyReportItem,
    NotionSyncRequest,
    RuleCreate,
    RuleRead,
    TransactionRead,
)
from .notion_sync import sync_transactions_to_notion

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure SaaS Accountant MVP")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.post("/accounts", response_model=AccountRead)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(
        db=db, name=account.name, provider=account.provider, institution=account.institution
    )


@app.get("/accounts", response_model=List[AccountRead])
def list_accounts(db: Session = Depends(get_db)):
    return crud.get_accounts(db)


@app.post("/ingest/mock")
def ingest_mock(payload: IngestMockRequest, db: Session = Depends(get_db)):
    account = crud.get_account(db, account_id=payload.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    data_path = Path(__file__).resolve().parent.parent / "sample_data" / "transactions_td_demo.json"
    if not data_path.exists():
        raise HTTPException(status_code=500, detail="Sample data missing")

    with data_path.open() as f:
        raw_transactions = json.load(f)

    normalized = [
        {
            "id": txn["id"],
            "date": dt.datetime.fromisoformat(txn["date"]).date(),
            "amount": txn["amount"],
            "currency": txn.get("currency", "CAD"),
            "merchant": txn.get("merchant", ""),
            "raw_category": txn.get("raw_category"),
            "category": None,
            "bucket": None,
            "source_system": txn.get("source_system", account.provider),
        }
        for txn in raw_transactions
    ]

    inserted = crud.bulk_insert_transactions(db, account, normalized)
    return {"inserted": inserted, "total": len(normalized)}


@app.get("/transactions", response_model=List[TransactionRead])
def list_transactions(
    account_id: Optional[int] = None,
    from_date: Optional[dt.date] = Query(default=None, alias="from"),
    to_date: Optional[dt.date] = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
):
    return crud.get_transactions(db, account_id=account_id, date_from=from_date, date_to=to_date)


@app.post("/rules", response_model=RuleRead)
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    return crud.create_rule(
        db=db,
        pattern=rule.pattern,
        field=rule.field,
        category=rule.category,
        bucket=rule.bucket,
        priority=rule.priority,
        enabled=rule.enabled,
    )


@app.get("/rules", response_model=List[RuleRead])
def list_rules(db: Session = Depends(get_db)):
    return crud.get_rules(db)


@app.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    removed = crud.delete_rule(db, rule_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"deleted": True}


@app.post("/apply-rules")
def apply_rules(payload: ApplyRulesRequest, db: Session = Depends(get_db)):
    count = crud.apply_rules(db, account_id=payload.account_id)
    return {"processed": count}


@app.post("/budgets", response_model=BudgetRead)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    return crud.create_budget(
        db=db,
        bucket=budget.bucket,
        monthly_limit=budget.monthly_limit,
        currency=budget.currency,
        alert_threshold=budget.alert_threshold,
    )


@app.get("/budgets", response_model=List[BudgetRead])
def list_budgets(db: Session = Depends(get_db)):
    return crud.get_budgets(db)


@app.get("/reports/monthly", response_model=List[MonthlyReportItem])
def monthly_report(year: int, month: int, account_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.monthly_report(db, year=year, month=month, account_id=account_id)


@app.post("/notion/sync")
def sync_notion(payload: NotionSyncRequest, db: Session = Depends(get_db)):
    txns = crud.get_transactions(
        db,
        account_id=payload.account_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    return sync_transactions_to_notion(txns)


@app.get("/demo", response_class=HTMLResponse)
def demo_page(request: Request, db: Session = Depends(get_db)):
    """
    Demo GUI: shows high-level summary and a table of categorized transactions.
    This uses ONLY mock/sample data and represents a Secure SaaS Accountant MVP.
    """
    total_value = db.query(func.sum(Transaction.amount)).scalar() or 0
    total_spend = float(total_value)

    bucket_rows = (
        db.query(
            Transaction.bucket.label("bucket"),
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(Transaction.bucket.isnot(None))
        .group_by(Transaction.bucket)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    bucket_summaries = [
        {"bucket": row.bucket or "Uncategorized", "tx_count": row.count, "total": float(row.total or 0)}
        for row in bucket_rows
    ]

    transactions = (
        db.query(Transaction)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(50)
        .all()
    )

    return templates.TemplateResponse(
        "demo.html",
        {
            "request": request,
            "headline": "Secure SaaS Accountant (MCP-ready, Sample Mode)",
            "subheadline": "Mock TD / PayPal-style transactions • Rules-based categorization • MCP orchestration • No real bank connection.",
            "total_spend": total_spend,
            "buckets": bucket_summaries,
            "transactions": transactions,
        },
    )


@app.get("/")
def healthcheck():
    return {"status": "ok"}
