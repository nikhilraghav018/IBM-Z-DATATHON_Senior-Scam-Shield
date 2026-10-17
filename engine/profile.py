"""Learns what "normal" looks like for one customer from their history.

The engine compares new events against this profile, so a $9,000 cash withdrawal
is unusual for someone who normally takes out $200, but not for someone who
regularly takes out $5,000.
"""

from collections import Counter

from engine import config
from engine.parsing import to_amount


def build_profile(history):
    """Return {"normal_transfer", "normal_cash", "payee_counts"} from a list of history Events."""
    transfers = [
        to_amount(e.get("amount"))
        for e in history
        if e.get("type") == "internal_transfer" and e.get("to_account") == "checking"
    ]
    cash = [to_amount(e.get("amount")) for e in history if e.get("type") == "cash_withdrawal"]
    payee_counts = Counter(
        e["payee_id"]
        for e in history
        if e.get("type") in ("wire", "payment") and e.get("payee_id")
    )
    return {
        # Spec: "normal" = the largest amount of that type seen in history.
        "normal_transfer": max(transfers) if transfers else config.DEFAULT_NORMAL_TRANSFER,
        "normal_cash": max(cash) if cash else config.DEFAULT_NORMAL_CASH,
        "payee_counts": payee_counts,
    }
