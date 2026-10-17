"""Checks one event and works out which triggers it fires.

Triggers (docs/DECISION_SPEC.md, Step 1):
  T1  unusual move           big savings/investment -> checking transfer, or big cash withdrawal
  T2  risky destination      gold / crypto payee, or a large first payment to a new payee
  T3  repeat                 another large outflow within 7 days of a previous one
  T5  workaround             a large outflow after the bank already paused/held something
  RA  remote access          money moved during a session with remote-control software
T4 is not a trigger: it is the "bank already stepped in" state, passed in as `intervention_active`.
"""

from datetime import timedelta

from engine import config


def is_trusted_payee(event, profile):
    """Step 0: verified billers, or payees the customer has paid 2+ times before, skip every trigger."""
    if event.get("type") not in ("wire", "payment"):
        return False
    if event.get("payee_verified"):
        return True
    count = profile["payee_counts"].get(event.get("payee_id"), 0)
    return count >= config.TRUSTED_PAYEE_MIN_PAYMENTS


def is_large_outflow(event):
    return event.get("type") in config.OUTFLOW_TYPES and event["amount"] >= config.LARGE_OUTFLOW


def check_t1(event, profile):
    """Unusual move: more than 5x this customer's normal AND more than $5,000."""
    amount = event["amount"]
    if (
        event.get("type") == "internal_transfer"
        and event.get("from_account") in ("savings", "investment")
        and event.get("to_account") == "checking"
    ):
        return amount > max(config.T1_MULTIPLIER * profile["normal_transfer"], config.T1_FLOOR)
    if event.get("type") == "cash_withdrawal":
        return amount > max(config.T1_MULTIPLIER * profile["normal_cash"], config.T1_FLOOR)
    return False


def check_t2(event, profile):
    """Risky destination: gold/crypto payee, or a new payee receiving $10,000+."""
    if event.get("type") not in ("wire", "payment"):
        return False
    if event.get("payee_category") in config.RISKY_CATEGORIES:
        return True
    is_new = profile["payee_counts"].get(event.get("payee_id"), 0) == 0
    return is_new and event["amount"] >= config.T2_NEW_PAYEE_MIN


def check_t3(event, recent):
    """Repeat: a large outflow when there was another large outflow in the last 7 days.

    `recent` holds this customer's earlier records. Attempts count even if the bank paused
    them. Payments to trusted payees never count (a big tax payment isn't a scam step).
    """
    if not is_large_outflow(event):
        return False
    cutoff = event["_ts"] - timedelta(days=config.REPEAT_DAYS)
    return any(r["large_outflow"] and r["ts"] >= cutoff for r in recent)


def check_t5(event, intervention_active):
    """Workaround: any large outflow while the bank has stepped in within the last 7 days."""
    return is_large_outflow(event) and intervention_active


def check_ra(event, ra_dates):
    """Remote access: this event moves money and remote-control software was seen today."""
    if event.get("type") not in config.MONEY_TYPES:
        return False
    return bool(event.get("remote_access")) or event["_ts"].date() in ra_dates


def fired_triggers(event, profile, recent, intervention_active, ra_dates):
    """Return the set of triggers this event fires (empty set if it's trusted or harmless)."""
    if event.get("type") == "login" or is_trusted_payee(event, profile):
        return set()
    fired = set()
    if check_t1(event, profile):
        fired.add("T1")
    if check_t2(event, profile):
        fired.add("T2")
    if check_t3(event, recent):
        fired.add("T3")
    if check_t5(event, intervention_active):
        fired.add("T5")
    if check_ra(event, ra_dates):
        fired.add("RA")
    return fired
