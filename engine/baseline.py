"""The comparison: what a bank's usual single-transaction check would do.

Today's fraud checks score one payment at a time. This is a fair, simple version of that:
flag a very large outflow, or a large wire to a payee the customer has never used.
It has no memory, so it cannot see a sequence building up over days.

Used by replay.py to show what our chain catches that a single-transaction rule misses.
"""

from engine import config
from engine.parsing import clean_event
from engine.profile import build_profile

# A single outflow at or above this is flagged on its own.
SINGLE_OUTFLOW_FLAG = 50000
# A wire at or above this to a payee the customer has never paid is flagged.
NEW_PAYEE_WIRE_FLAG = 25000


class SingleTransactionBaseline:
    """Same interface as Engine, so replay.py can run both over the same events."""

    def __init__(self):
        self.profiles = {}

    def register(self, customer, history):
        self.profiles[customer["customer_id"]] = build_profile(history)

    def process(self, event):
        ev = clean_event(event)
        profile = self.profiles.get(ev["customer_id"], {"payee_counts": {}})
        flagged, reason = False, "Allowed: nothing unusual about this single transaction"

        if ev.get("type") in config.OUTFLOW_TYPES:
            if ev["amount"] >= SINGLE_OUTFLOW_FLAG:
                flagged = True
                reason = f"Flagged: single outflow of ${ev['amount']:,.0f}"
            elif (
                ev.get("type") == "wire"
                and ev["amount"] >= NEW_PAYEE_WIRE_FLAG
                and profile["payee_counts"].get(ev.get("payee_id"), 0) == 0
            ):
                flagged = True
                reason = f"Flagged: ${ev['amount']:,.0f} wire to a first-time payee"

        return {
            "event_id": ev["event_id"],
            "customer_id": ev["customer_id"],
            "timestamp": ev["timestamp"],
            "action": "pause" if flagged else "allow",
            "reasons": [reason],
            "money_released": not flagged,
        }
