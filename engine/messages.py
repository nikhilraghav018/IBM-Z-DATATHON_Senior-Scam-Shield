"""Plain-English reasons and the customer / staff / family messages.

Templates come from docs/DECISION_SPEC.md ("Message templates" and "Reasons").
Family messages never contain amounts, payees or account details.
"""

from datetime import timedelta

from engine import config

CUSTOMER = {
    "allow": None,
    "warn": (
        "Reminder: your bank, the police and government agencies will never ask you to move "
        "money to keep it safe, buy gold, or hand cash to a courier."
    ),
    "pause": (
        "We've paused this payment to protect you. A member of our team will call you at the "
        "phone number we have on file."
    ),
    "hold": "This payment is on a short hold while we make sure you are safe. We will call you today.",
    "escalate": "This payment is still on hold. A branch manager will contact you personally.",
}

STAFF = {
    "allow": None,
    "warn": None,
    "pause": (
        "PAUSE: call the customer on the number on file, not one they give you. Ask: Has anyone "
        "asked you to keep this payment secret, or told you what to say to the bank?"
    ),
    "hold": (
        "HOLD: senior scam pattern. Call the customer, then the trusted contact. Do not release "
        "funds until verified."
    ),
    "escalate": (
        "ESCALATE: repeated attempts after a hold. Manager review required. Consider an Adult "
        "Protective Services referral."
    ),
}

FAMILY = (
    "Hi {contact}, {first} asked us to let you know if something looked unusual. "
    "Please check in with them today."
)

CATEGORY_NAMES = {
    "gold_dealer": "gold dealer",
    "crypto_exchange": "crypto exchange",
    "crypto_atm": "crypto ATM",
}


def money(amount):
    return f"${amount:,.0f}"


def day(event):
    return event["_ts"].strftime("%b %d").replace(" 0", " ")


def family_message(customer, action):
    contact = customer.get("trusted_contact")
    if action not in config.HOLD_ACTIONS or not customer.get("opted_in") or not contact:
        return None
    return FAMILY.format(contact=contact["name"].split()[0], first=customer["name"].split()[0])


def allow_reason(event, profile):
    if event.get("type") == "login":
        if event.get("remote_access"):
            return "Remote-access software detected at login; watching this session"
        return "Normal login"
    if event.get("payee_verified") and event.get("type") in ("wire", "payment"):
        return f"Verified payee ({event.get('payee_name')})"
    count = profile["payee_counts"].get(event.get("payee_id"), 0)
    if count >= config.TRUSTED_PAYEE_MIN_PAYMENTS:
        return f"Trusted payee, paid {count} times before"
    return "Normal activity for this customer"


def trigger_reason(trigger, record, profile, recent):
    """One plain-English line explaining why `trigger` fired on `record`'s event."""
    e = record["event"]
    if trigger == "T1":
        if e.get("type") == "internal_transfer":
            ratio = round(e["amount"] / profile["normal_transfer"])
            return (
                f"{day(e)}: {money(e['amount'])} moved from {e['from_account']} to checking "
                f"(about {ratio}x this customer's usual transfer)"
            )
        ratio = round(e["amount"] / profile["normal_cash"])
        return f"{day(e)}: {money(e['amount'])} cash withdrawal (about {ratio}x their usual)"
    if trigger == "T2":
        category = CATEGORY_NAMES.get(e.get("payee_category"), "new payee")
        seen_before = profile["payee_counts"].get(e.get("payee_id"), 0) > 0 or any(
            r["event"].get("payee_id") == e.get("payee_id") for r in recent
        )
        first = "payment" if seen_before else "first payment"
        return f"{day(e)}: {first} to a {category} ({e.get('payee_name')}, {money(e['amount'])})"
    if trigger == "T3":
        cutoff = e["_ts"] - timedelta(days=config.REPEAT_DAYS)
        earlier = [r for r in recent if r["large_outflow"] and r["ts"] >= cutoff]
        gap_days = max(1, round((e["_ts"] - earlier[-1]["ts"]).total_seconds() / 86400))
        total = e["amount"] + sum(r["event"]["amount"] for r in earlier)
        unit = "day" if gap_days == 1 else "days"
        return (
            f"{day(e)}: another large outflow within {gap_days} {unit} "
            f"({money(total)} in the last 7 days)"
        )
    if trigger == "RA":
        return f"{day(e)}: remote-access software was active during this session"
    if trigger == "T5":
        return f"{day(e)}: new attempt to move money after the bank already stepped in"
    return f"{day(e)}: {trigger}"
