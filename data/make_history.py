#!/usr/bin/env python3
"""Generate realistic normal-history events for a Senior Scam Shield customer.

This script produces a history array of Event objects with truth='normal'
for the 60-90 days before the story week. It intentionally keeps the output
simple and deterministic so scenario JSON files stay easy to review.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PAYEE_LIBRARY = {
    "grocery": [
        ("P-KRG", "Kroger", False),
        ("P-SAF", "Safeway", False),
        ("P-HMF", "H-E-B", False),
    ],
    "pharmacy": [
        ("P-CVS", "CVS Pharmacy", False),
        ("P-WAL", "Walgreens", False),
    ],
    "utility": [
        ("P-ATM", "Atmos Energy", True),
        ("P-PEC", "CenterPoint Energy", True),
        ("P-WTR", "Water Utility", True),
    ],
    "gold_dealer": [
        ("P-HER", "Heritage Coins", False),
    ],
    "crypto": [
        ("P-CBX", "Coinbase", False),
    ],
}


def isoformat(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def add_event(
    history: List[Dict[str, Any]],
    customer_id: str,
    timestamp: datetime,
    event_type: str,
    amount: float,
    *,
    from_account: Optional[str] = None,
    to_account: Optional[str] = None,
    payee_id: Optional[str] = None,
    payee_name: Optional[str] = None,
    payee_category: Optional[str] = None,
    payee_verified: bool = False,
    branch_id: Optional[str] = None,
    remote_access: bool = False,
) -> None:
    """Append a valid Event record with the required contract fields."""
    event = {
        "event_id": f"{customer_id}-H{len(history) + 1:03d}",
        "customer_id": customer_id,
        "timestamp": isoformat(timestamp),
        "type": event_type,
        "channel": "online",
        "amount": float(amount),
        "from_account": from_account,
        "to_account": to_account,
        "payee_id": payee_id,
        "payee_name": payee_name,
        "payee_category": payee_category,
        "payee_verified": payee_verified,
        "branch_id": branch_id,
        "remote_access": remote_access,
        "truth": "normal",
    }

    if event_type in {"cash_withdrawal", "payment", "wire"}:
        event["channel"] = "atm" if event_type == "cash_withdrawal" else "online"
    elif event_type == "internal_transfer":
        event["channel"] = "online"
    elif event_type == "login":
        event["amount"] = 0
        event["channel"] = "online"
    elif event_type == "deposit":
        event["channel"] = "online"
        event["to_account"] = "checking"
        event["from_account"] = None

    if event_type == "cash_withdrawal":
        event["branch_id"] = branch_id or "BR-HOME-1"

    history.append(event)


def generate_monthly_deposit(history: List[Dict[str, Any]], customer_id: str, month_start: datetime, rng: random.Random) -> None:
    deposit_amounts = [2200, 2600, 2300, 2400, 3000, 3200, 2800]
    for offset_days in [1, 18, 30]:
        dt = month_start + timedelta(days=offset_days)
        add_event(
            history,
            customer_id,
            dt,
            "deposit",
            rng.choice(deposit_amounts),
            payee_name="Social Security",
            payee_category=None,
            payee_verified=False,
        )


def generate_weekly_bills(history: List[Dict[str, Any]], customer_id: str, start_date: datetime, rng: random.Random) -> None:
    dt = start_date
    while dt < start_date + timedelta(days=90):
        if dt.weekday() in {1, 3, 5}:
            category = "grocery"
            payee_id, payee_name, verified = rng.choice(PAYEE_LIBRARY[category])
            add_event(
                history,
                customer_id,
                dt + timedelta(hours=12 + rng.randint(0, 5)),
                "payment",
                round(rng.uniform(40, 180), 2),
                from_account="checking",
                payee_id=payee_id,
                payee_name=payee_name,
                payee_category=category,
                payee_verified=verified,
            )

        if dt.weekday() == 2:
            payee_id, payee_name, verified = rng.choice(PAYEE_LIBRARY["pharmacy"])
            add_event(
                history,
                customer_id,
                dt + timedelta(hours=10 + rng.randint(0, 3)),
                "payment",
                round(rng.uniform(25, 90), 2),
                from_account="checking",
                payee_id=payee_id,
                payee_name=payee_name,
                payee_category="pharmacy",
                payee_verified=verified,
            )

        if dt.day in {5, 12, 20, 28}:
            payee_id, payee_name, verified = rng.choice(PAYEE_LIBRARY["utility"])
            add_event(
                history,
                customer_id,
                dt + timedelta(hours=8 + rng.randint(0, 2)),
                "payment",
                round(rng.uniform(90, 220), 2),
                from_account="checking",
                payee_id=payee_id,
                payee_name=payee_name,
                payee_category="utility",
                payee_verified=verified,
            )

        dt += timedelta(days=1)


def generate_atm_history(history: List[Dict[str, Any]], customer_id: str, start_date: datetime, rng: random.Random) -> None:
    dt = start_date
    while dt < start_date + timedelta(days=90):
        if dt.weekday() in {0, 2, 4} and rng.random() < 0.35:
            add_event(
                history,
                customer_id,
                dt + timedelta(hours=8 + rng.randint(0, 5)),
                "cash_withdrawal",
                rng.choice([120, 150, 200, 250, 300]),
                from_account="checking",
                branch_id="BR-HOME-1",
            )
        dt += timedelta(days=1)


def generate_small_transfers(history: List[Dict[str, Any]], customer_id: str, start_date: datetime, rng: random.Random) -> None:
    dt = start_date
    while dt < start_date + timedelta(days=90):
        if dt.weekday() in {6} and rng.random() < 0.55:
            amount = rng.choice([500, 700, 1000, 1200, 1500])
            add_event(
                history,
                customer_id,
                dt + timedelta(hours=9 + rng.randint(0, 4)),
                "internal_transfer",
                amount,
                from_account="savings",
                to_account="checking",
            )
        dt += timedelta(days=1)


def generate_customer_specific_history(
    history: List[Dict[str, Any]], customer_id: str, start_date: datetime, rng: random.Random
) -> None:
    """Add scenario-specific normal history for the innocent look-alikes."""
    if customer_id == "C5":
        for day in range(0, 90, 18):
            dt = start_date + timedelta(days=day)
            payee_id, payee_name, verified = PAYEE_LIBRARY["gold_dealer"][0]
            add_event(
                history,
                customer_id,
                dt + timedelta(hours=14),
                "payment",
                rng.choice([2000, 2500, 3000, 4000]),
                from_account="checking",
                payee_id=payee_id,
                payee_name=payee_name,
                payee_category="gold_dealer",
                payee_verified=verified,
            )

    if customer_id == "C7":
        for day in range(10, 90, 21):
            dt = start_date + timedelta(days=day)
            payee_id, payee_name, verified = PAYEE_LIBRARY["crypto"][0]
            add_event(
                history,
                customer_id,
                dt + timedelta(hours=15),
                "payment",
                rng.choice([300, 420, 550, 700]),
                from_account="checking",
                payee_id=payee_id,
                payee_name=payee_name,
                payee_category="crypto_exchange",
                payee_verified=verified,
            )


def generate_history(customer_id: str, start_date: str = "2026-07-01", days: int = 90, seed: int = 42) -> List[Dict[str, Any]]:
    """Create a realistic sequence of normal events for a customer.

    The resulting object is suitable to be inserted into a scenario file under
    the `history` field.
    """
    rng = random.Random(seed)
    history: List[Dict[str, Any]] = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    for month_offset in range(3):
        month_start = start_dt + timedelta(days=month_offset * 30)
        generate_monthly_deposit(history, customer_id, month_start, rng)

    generate_weekly_bills(history, customer_id, start_dt, rng)
    generate_atm_history(history, customer_id, start_dt, rng)
    generate_small_transfers(history, customer_id, start_dt, rng)
    generate_customer_specific_history(history, customer_id, start_dt, rng)

    # Sort final output by timestamp, then reindex event IDs for easier review.
    history.sort(key=lambda item: item["timestamp"])
    for i, event in enumerate(history, start=1):
        event["event_id"] = f"{customer_id}-H{i:03d}"

    return history


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate normal bank-history events for a customer.")
    parser.add_argument("customer_id", nargs="?", default="C1", help="Customer ID, such as C1 or C5")
    parser.add_argument("--start-date", default="2026-07-01", help="History start date in YYYY-MM-DD format")
    parser.add_argument("--days", type=int, default=90, help="Number of days to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic output")
    parser.add_argument("--output", help="Optional path to write the JSON array to a file")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    history = generate_history(args.customer_id, start_date=args.start_date, days=args.days, seed=args.seed)
    output = json.dumps(history, indent=2)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
        print(f"Wrote {len(history)} history events to {out_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
