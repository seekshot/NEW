from typing import List

from .models import Rule, Transaction


def apply_rules_to_transactions(transactions: List[Transaction], rules: List[Rule]) -> None:
    """
    Mutates each Transaction in-place with category and bucket if a Rule matches.
    Rules are applied in order of priority (highest first). The first matching rule wins.
    """
    sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

    for txn in transactions:
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            value = getattr(txn, rule.field, None)
            if value is None:
                continue
            if rule.pattern.lower() in str(value).lower():
                txn.category = rule.category
                txn.bucket = rule.bucket
                break
