from typing import List

from .models import Transaction


def sync_transactions_to_notion(transactions: List[Transaction]) -> dict:
    """
    Stub function for Notion sync.
    For now, just return a summary dict and DO NOT call any external APIs.
    """
    created = len(transactions)
    updated = 0
    return {"created": created, "updated": updated}
