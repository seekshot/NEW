import datetime as dt
from typing import Iterable, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .models import Account, Budget, Rule, Transaction
from .rules import apply_rules_to_transactions


# Accounts

def get_accounts(db: Session) -> List[Account]:
    return db.query(Account).all()


def create_account(db: Session, name: str, provider: str, institution: str) -> Account:
    account = Account(name=name, provider=provider, institution=institution, last_sync=None)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_account(db: Session, account_id: int) -> Optional[Account]:
    return db.query(Account).filter(Account.id == account_id).first()


# Transactions

def get_transactions(
    db: Session,
    account_id: Optional[int] = None,
    date_from: Optional[dt.date] = None,
    date_to: Optional[dt.date] = None,
) -> List[Transaction]:
    query = db.query(Transaction)
    filters = []
    if account_id is not None:
        filters.append(Transaction.account_id == account_id)
    if date_from is not None:
        filters.append(Transaction.date >= date_from)
    if date_to is not None:
        filters.append(Transaction.date <= date_to)
    if filters:
        query = query.filter(and_(*filters))
    return query.order_by(Transaction.date.desc()).all()


def bulk_insert_transactions(db: Session, account: Account, txns: Iterable[dict]) -> int:
    inserted = 0
    for txn in txns:
        exists = db.query(Transaction).filter(Transaction.id == txn["id"]).first()
        if exists:
            continue
        record = Transaction(
            id=txn["id"],
            account_id=account.id,
            date=txn["date"],
            amount=txn["amount"],
            currency=txn["currency"],
            merchant=txn.get("merchant", ""),
            raw_category=txn.get("raw_category"),
            category=txn.get("category"),
            bucket=txn.get("bucket"),
            source_system=txn.get("source_system", account.provider),
        )
        db.add(record)
        inserted += 1
    account.last_sync = dt.datetime.utcnow()
    db.commit()
    return inserted


# Rules

def get_rules(db: Session) -> List[Rule]:
    return db.query(Rule).order_by(Rule.priority.desc()).all()


def create_rule(
    db: Session, pattern: str, field: str, category: str, bucket: str, priority: int, enabled: bool
) -> Rule:
    rule = Rule(
        pattern=pattern,
        field=field,
        category=category,
        bucket=bucket,
        priority=priority,
        enabled=enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: int) -> bool:
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        return False
    db.delete(rule)
    db.commit()
    return True


def apply_rules(db: Session, account_id: Optional[int] = None, date_from: Optional[dt.date] = None) -> int:
    rules = get_rules(db)
    transactions = get_transactions(db, account_id=account_id, date_from=date_from)
    apply_rules_to_transactions(transactions, rules)
    db.commit()
    return len(transactions)


# Budgets

def get_budgets(db: Session) -> List[Budget]:
    return db.query(Budget).all()


def create_budget(db: Session, bucket: str, monthly_limit: float, currency: str, alert_threshold: float) -> Budget:
    budget = Budget(
        bucket=bucket,
        monthly_limit=monthly_limit,
        currency=currency,
        alert_threshold=alert_threshold,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


# Reports

def monthly_report(db: Session, year: int, month: int, account_id: Optional[int] = None):
    start = dt.date(year, month, 1)
    if month == 12:
        end = dt.date(year + 1, 1, 1)
    else:
        end = dt.date(year, month + 1, 1)

    query = db.query(Transaction.bucket, func.sum(Transaction.amount).label("total"))
    query = query.filter(Transaction.date >= start, Transaction.date < end)
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    query = query.group_by(Transaction.bucket)

    spend_by_bucket = {row.bucket or "Uncategorized": float(row.total or 0) for row in query.all()}
    budgets = {b.bucket: b for b in get_budgets(db)}

    report_items = []
    for bucket, total in spend_by_bucket.items():
        budget = budgets.get(bucket)
        limit = float(budget.monthly_limit) if budget else None
        utilization = (total / limit) if limit else None
        over_budget = utilization is not None and utilization > 1
        report_items.append(
            {
                "bucket": bucket,
                "total_spend": total,
                "limit": limit,
                "utilization": utilization,
                "over_budget": over_budget,
            }
        )

    return report_items
