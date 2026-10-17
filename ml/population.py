"""A synthetic bank population for training the ML risk score. Standard library only.

The 8 demo scenarios hold only 18 live events, which is a demo, not a training set.
This module generates thousands of customers instead:

- Everyone gets ~90 days of normal history from Shums's `data/make_history.py`, rescaled
  per customer so "normal" differs between people (some take out $150 cash, some $1,500).
- Everyone gets a normal live fortnight (groceries, pharmacy, ATM cash, small transfers).
- A share of customers also get an innocent look-alike event (house purchase, tax bill,
  car bought with cash, a contractor, a gift to family, ...). These are the hard negatives.
- About 2% get a scam chain injected, one of the three patterns in docs/SCENARIOS.md,
  with randomised amounts, gaps, branches, payees and early stops.

Each event carries `truth` ("scam" or "normal"). Only the training code reads it;
the engine never sees it (engine/parsing.py strips it).

Customers are generated one at a time (`iter_population`) so memory stays small on the
7.8 GB LinuxONE box. `build_dataset` runs them through the real engine and returns one
feature row per live event, using `Engine.features()` via the scorer hook, so the model
sees exactly what the rules see.
"""

import importlib.util
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCAM_TYPES = ("gold_bar", "grandparent", "phantom_hacker")
LOOKALIKE_TYPES = (
    "home_buyer", "coin_collector", "car_buyer", "crypto_investor", "tax_payment",
    "contractor", "family_gift",
)

LIVE_START = datetime(2026, 10, 19, 8, 0)
LIVE_DAYS = 14
CITIES = ("FRISCO", "PLANO", "DALLAS", "AUSTIN", "IRVING", "MCKINNEY", "DENTON", "ALLEN")
GOLD_DEALERS = ("Lone Star Bullion", "Texas Gold Exchange", "Patriot Precious Metals", "Liberty Coin Vault")


def _load_make_history():
    """Import data/make_history.py by path (data/ is not a package)."""
    spec = importlib.util.spec_from_file_location("make_history", ROOT / "data" / "make_history.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


make_history = _load_make_history()


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


class _Builder:
    """Collects one customer's live events with contract-shaped fields."""

    def __init__(self, cid):
        self.cid = cid
        self.events = []

    def add(self, ts, type_, amount, truth, channel="online", **fields):
        event = {
            "event_id": f"{self.cid}-E{len(self.events) + 1:03d}",
            "customer_id": self.cid,
            "timestamp": _iso(ts),
            "type": type_,
            "channel": channel,
            "amount": round(float(amount), 2),
            "from_account": fields.get("from_account", None if type_ in ("deposit", "login") else "checking"),
            "to_account": fields.get("to_account"),
            "payee_id": fields.get("payee_id"),
            "payee_name": fields.get("payee_name"),
            "payee_category": fields.get("payee_category"),
            "payee_verified": fields.get("payee_verified", False),
            "branch_id": fields.get("branch_id"),
            "remote_access": fields.get("remote_access", False),
            "truth": truth,
        }
        self.events.append(event)
        return event


def _history(cid, rng, wealth, home_branch, kind):
    """Shums's normal history, rescaled for this customer, plus the look-alikes' habits."""
    history = make_history.generate_history(cid, start_date="2026-07-20", seed=rng.randrange(10**9))
    for e in history:
        if e["type"] in ("cash_withdrawal", "internal_transfer"):
            e["amount"] = round(e["amount"] * wealth, 2)
        if e["type"] == "cash_withdrawal":
            e["branch_id"] = home_branch
    start = datetime(2026, 7, 20, 14, 0)
    if kind == "coin_collector":
        for day in range(0, 90, rng.choice((15, 18, 25))):
            history.append(_hist_payment(cid, start + timedelta(days=day), rng.choice((2000, 2500, 3000, 4000)) * wealth,
                                         "P-HER", "Heritage Coins", "gold_dealer"))
    if kind == "crypto_investor":
        for day in range(5, 90, rng.choice((14, 21, 30))):
            history.append(_hist_payment(cid, start + timedelta(days=day), rng.choice((300, 420, 550, 700)) * wealth,
                                         "P-CBX", "Coinbase", "crypto_exchange"))
    history.sort(key=lambda e: e["timestamp"])
    return history


def _hist_payment(cid, ts, amount, payee_id, payee_name, category):
    return {
        "event_id": f"{cid}-HX{ts:%m%d}", "customer_id": cid, "timestamp": _iso(ts), "type": "payment",
        "channel": "online", "amount": round(amount, 2), "from_account": "checking", "to_account": None,
        "payee_id": payee_id, "payee_name": payee_name, "payee_category": category, "payee_verified": False,
        "branch_id": None, "remote_access": False, "truth": "normal",
    }


def _normal_fortnight(b, rng, wealth, home_branch):
    """Everyday life during the live window, labelled normal."""
    for day in range(LIVE_DAYS):
        date = LIVE_START + timedelta(days=day)
        if date.weekday() in (1, 3, 5) and rng.random() < 0.8:
            pid, name, verified = rng.choice(make_history.PAYEE_LIBRARY["grocery"])
            b.add(date + timedelta(hours=rng.randint(2, 9)), "payment", rng.uniform(40, 180), "normal",
                  payee_id=pid, payee_name=name, payee_category="grocery", payee_verified=verified)
        if date.weekday() == 2 and rng.random() < 0.7:
            pid, name, verified = rng.choice(make_history.PAYEE_LIBRARY["pharmacy"])
            b.add(date + timedelta(hours=rng.randint(2, 6)), "payment", rng.uniform(25, 90), "normal",
                  payee_id=pid, payee_name=name, payee_category="pharmacy", payee_verified=verified)
        if date.weekday() in (0, 4) and rng.random() < 0.35:
            b.add(date + timedelta(hours=rng.randint(1, 6)), "cash_withdrawal",
                  rng.choice((120, 150, 200, 250, 300)) * wealth, "normal", channel="atm", branch_id=home_branch)
        if date.weekday() == 6 and rng.random() < 0.4:
            b.add(date + timedelta(hours=rng.randint(1, 5)), "internal_transfer",
                  rng.choice((500, 700, 1000, 1200, 1500)) * wealth, "normal",
                  from_account="savings", to_account="checking")
        if rng.random() < 0.15:
            b.add(date + timedelta(hours=rng.randint(0, 10)), "login", 0, "normal")


def _day(rng, lo=0, hi=LIVE_DAYS - 6):
    """A random morning inside the live window, leaving room for a chain to play out."""
    return LIVE_START + timedelta(days=rng.randint(lo, hi), hours=rng.randint(0, 8), minutes=rng.randint(0, 59))


def _lookalike(b, kind, rng, wealth, home_branch):
    """One innocent but unusual-looking episode. Labelled normal."""
    t = _day(rng)
    if kind == "home_buyer":
        amount = rng.uniform(60_000, 300_000)
        b.add(t, "internal_transfer", amount, "normal", from_account=rng.choice(("savings", "investment")),
              to_account="checking")
        b.add(t + timedelta(days=rng.randint(1, 4)), "wire", amount * rng.uniform(0.9, 1.0), "normal",
              payee_id=f"P-TIT{rng.randint(1, 40)}", payee_name="Title Company", payee_category="title_escrow",
              payee_verified=True)
    elif kind == "coin_collector":
        b.add(t, "payment", rng.choice((2000, 2500, 3000, 4000, 6000)) * wealth, "normal",
              payee_id="P-HER", payee_name="Heritage Coins", payee_category="gold_dealer")
    elif kind == "car_buyer":
        if rng.random() < 0.6:
            b.add(t, "cash_withdrawal", rng.uniform(8_000, 35_000), "normal", channel="branch", branch_id=home_branch)
        else:
            b.add(t, "wire", rng.uniform(15_000, 45_000), "normal", payee_id=f"P-AUTO{rng.randint(1, 50)}",
                  payee_name="Auto Dealer", payee_category="auto_dealer")
    elif kind == "crypto_investor":
        b.add(t, "payment", rng.choice((300, 420, 550, 700)) * wealth, "normal",
              payee_id="P-CBX", payee_name="Coinbase", payee_category="crypto_exchange")
    elif kind == "tax_payment":
        amount = rng.uniform(8_000, 50_000)
        b.add(t, "internal_transfer", amount, "normal", from_account="savings", to_account="checking")
        b.add(t + timedelta(days=rng.randint(1, 4)), "payment", amount * rng.uniform(0.85, 1.0), "normal",
              payee_id="P-IRS", payee_name="IRS", payee_category="government", payee_verified=True)
    elif kind == "contractor":
        b.add(t, "payment", rng.uniform(5_000, 25_000), "normal", payee_id=f"P-CON{rng.randint(1, 80)}",
              payee_name="Home Contractor", payee_category="contractor")
        if rng.random() < 0.4:
            b.add(t + timedelta(days=rng.randint(3, 6)), "payment", rng.uniform(2_000, 10_000), "normal",
                  payee_id=f"P-CON{rng.randint(81, 90)}", payee_name="Home Contractor", payee_category="contractor")
    elif kind == "family_gift":
        b.add(t, "wire", rng.uniform(5_000, 25_000), "normal", payee_id=f"P-FAM{rng.randint(1, 99)}",
              payee_name="Family member", payee_category="person")


def _scam(b, kind, rng, home_branch, city):
    """One scam chain following docs/SCENARIOS.md, randomised. Labelled scam.

    Chains can stop early (the victim gets suspicious, or runs out of money), so not
    every scam has every step.
    """
    t = _day(rng)
    other_branch = lambda: f"BR-{city}-{rng.randint(2, 9)}"
    if kind == "gold_bar":
        stash = rng.uniform(40_000, 300_000)
        b.add(t, "internal_transfer", stash, "scam", from_account=rng.choice(("investment", "savings")),
              to_account="checking")
        dealer = rng.choice(GOLD_DEALERS)
        pid = "P-" + "".join(w[0] for w in dealer.split())
        t += timedelta(days=rng.randint(1, 2), hours=rng.randint(0, 5))
        b.add(t, rng.choice(("wire", "wire", "payment")), stash * rng.uniform(0.4, 0.7), "scam",
              payee_id=pid, payee_name=dealer, payee_category="gold_dealer")
        if rng.random() < 0.85:
            t += timedelta(days=rng.randint(1, 3), hours=rng.randint(0, 5))
            b.add(t, "wire", stash * rng.uniform(0.2, 0.5), "scam", payee_id=pid, payee_name=dealer,
                  payee_category="gold_dealer")
            if rng.random() < 0.7:
                t += timedelta(days=rng.randint(1, 2), hours=rng.randint(0, 5))
                b.add(t, "cash_withdrawal", rng.uniform(10_000, 60_000), "scam", channel="branch",
                      branch_id=other_branch())
    elif kind == "grandparent":
        amount = rng.uniform(5_000, 12_000)
        for step in range(rng.choice((2, 3, 3, 4))):
            branch = other_branch() if (step > 0 or rng.random() < 0.5) else home_branch
            b.add(t, "cash_withdrawal", amount, "scam", channel="branch", branch_id=branch)
            amount *= rng.uniform(1.2, 2.0)
            t += timedelta(days=rng.randint(1, 3), hours=rng.randint(0, 6))
    elif kind == "phantom_hacker":
        b.add(t, "login", 0, "scam", remote_access=True)
        stash = rng.uniform(40_000, 300_000)
        t += timedelta(minutes=rng.randint(5, 40))
        b.add(t, "internal_transfer", stash, "scam", from_account=rng.choice(("savings", "investment")),
              to_account="checking", remote_access=rng.random() < 0.6)
        if rng.random() < 0.9:
            t += timedelta(days=rng.randint(0, 2), hours=rng.randint(2, 8))
            category = rng.choice(("unknown", "unknown", "person", "crypto_exchange"))
            b.add(t, "wire", stash * rng.uniform(0.6, 1.0), "scam", payee_id=f"P-SAFE{rng.randint(1, 99)}",
                  payee_name="Safe Account", payee_category=category)
            if rng.random() < 0.7:
                t += timedelta(days=rng.randint(1, 2), hours=rng.randint(0, 5))
                if rng.random() < 0.6:
                    b.add(t, "cash_withdrawal", rng.uniform(10_000, 50_000), "scam", channel="branch",
                          branch_id=other_branch())
                else:
                    b.add(t, "payment", rng.uniform(5_000, 30_000), "scam", payee_id=f"P-BTM{rng.randint(1, 50)}",
                          payee_name="Crypto ATM", payee_category="crypto_atm")


def make_customer(index, rng, scam_rate=0.02, lookalike_rate=0.12):
    """Return (kind, customer, history, live) for one synthetic customer."""
    roll = rng.random()
    if roll < scam_rate:
        kind = rng.choice(SCAM_TYPES)
    elif roll < scam_rate + lookalike_rate:
        kind = rng.choice(LOOKALIKE_TYPES)
    else:
        kind = "everyday"
    cid = f"S{index:05d}"
    city = rng.choice(CITIES)
    home_branch = f"BR-{city}-1"
    wealth = min(max(rng.lognormvariate(0, 0.6), 0.3), 6.0)
    customer = {
        "customer_id": cid, "name": f"Synthetic {cid}", "age": rng.randint(62, 92), "opted_in": True,
        "trusted_contact": {"name": "Family", "relation": "child", "phone": "+1-000-555-0000"},
        "home_branch": home_branch,
    }
    history = _history(cid, rng, wealth, home_branch, kind)
    b = _Builder(cid)
    _normal_fortnight(b, rng, wealth, home_branch)
    if kind in SCAM_TYPES:
        _scam(b, kind, rng, home_branch, city)
    elif kind in LOOKALIKE_TYPES:
        _lookalike(b, kind, rng, wealth, home_branch)
    live = sorted(b.events, key=lambda e: e["timestamp"])
    return kind, customer, history, live


def iter_population(n=6000, seed=7, scam_rate=0.02, lookalike_rate=0.12):
    """Yield customers one at a time: (kind, customer, history, live)."""
    rng = random.Random(seed)
    for i in range(n):
        yield make_customer(i, rng, scam_rate, lookalike_rate)


def build_dataset(customers):
    """Run customers through the real engine and return one row per live event.

    Each row: {"customer_id", "kind", "event_id", "truth", "action", "features": {...}}.
    The features come from MLEngine.features() through the scorer hook, so they are exactly
    what the rules see (plus payee trust, see ml/features.py). `truth` is copied from the
    event here, never passed to the engine.
    """
    from ml.features import MLEngine

    captured = []
    engine = MLEngine(scorer=lambda features: captured.append(features) or {})
    rows = []
    for kind, customer, history, live in customers:
        engine.register(customer, history)
        for event in live:
            decision = engine.process(event)
            rows.append({
                "customer_id": customer["customer_id"],
                "kind": kind,
                "event_id": event["event_id"],
                "truth": event["truth"],
                "action": decision["action"],
                "features": captured.pop(),
            })
        # Free this customer's memory; we never come back to them.
        del engine.customers[customer["customer_id"]]
    return rows
