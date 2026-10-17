"""The decision engine: turns each Event into a Decision (docs/CONTRACT.md).

Interface used by api/main.py, keep these names stable:
    eng = Engine()
    eng.register(customer, history)   # once per customer
    decision = eng.process(event)     # one event at a time, in time order per customer

Pure Python standard library, so it runs on LinuxONE (s390x) with no installs.
"""

from datetime import datetime, timedelta

from engine import config, messages
from engine.profile import build_profile
from engine.triggers import fired_triggers, is_large_outflow, is_trusted_payee

CHAIN_ORDER = ("T1", "T2", "T3", "RA")


class Engine:
    def __init__(self):
        # customer_id -> {"customer", "profile", "records", "ra_dates"}
        self.customers = {}

    def register(self, customer, history):
        """Learn a customer's normal behaviour from their history. Call once before their events."""
        self.customers[customer["customer_id"]] = {
            "customer": customer,
            "profile": build_profile(history),
            "records": [],  # this customer's processed live events (last 7 days kept)
            "ra_dates": set(),  # days with a remote-access login
        }

    def process(self, event):
        """Decide what the bank should do about one event. Returns a Decision dict."""
        cid = event["customer_id"]
        if cid not in self.customers:
            raise KeyError(f"customer {cid} is not registered; call register() first")
        state = self.customers[cid]
        customer, profile = state["customer"], state["profile"]

        # Work on a copy so we never change the caller's event. Never read event["truth"].
        ev = {k: v for k, v in event.items() if k != "truth"}
        ev["_ts"] = now = datetime.fromisoformat(ev["timestamp"])

        recent = self._recent(state, now)
        intervention_active = any(
            r["action"] in config.INTERVENTION_ACTIONS
            and r["ts"] >= now - timedelta(days=config.WORKAROUND_DAYS)
            for r in recent
        )
        hold_active = any(r["action"] in config.HOLD_ACTIONS for r in recent)

        if ev["type"] == "login" and ev.get("remote_access"):
            state["ra_dates"].add(now.date())

        # Step 1: triggers. Each reason is written now, while "recent" is what came before.
        fired = fired_triggers(ev, profile, recent, intervention_active, state["ra_dates"])
        reasons_now = {t: messages.trigger_reason(t, {"event": ev}, profile, recent) for t in fired}

        # Step 2: the chain = distinct triggers over the last 7 days, including this event.
        in_chain = set(fired) - {"T5"}
        for r in recent:
            in_chain |= r["fired"] - {"T5"}
        chain = [t for t in CHAIN_ORDER if t in in_chain]

        action = self._pick_action(fired, chain, hold_active)

        # Step 3: opt-in cap. Without consent the bank never goes above "pause".
        if not customer.get("opted_in") and action in config.HOLD_ACTIONS:
            action = "pause"

        if action == "allow":
            reasons = [messages.allow_reason(ev, profile)]
        else:
            reasons = self._chain_reasons(chain, recent, reasons_now)
            if "T5" in fired:
                reasons.append(reasons_now["T5"])

        state["records"].append(
            {
                "ts": now,
                "event": ev,
                "fired": fired,
                "action": action,
                # Large outflows to untrusted payees are what T3 looks back for.
                "large_outflow": is_large_outflow(ev) and not is_trusted_payee(ev, profile),
                "reasons": reasons_now,
            }
        )

        score = sum(config.SCORE_WEIGHTS[t] for t in chain)
        if "T5" in fired:
            score += config.SCORE_T5_BONUS

        return {
            "event_id": ev["event_id"],
            "customer_id": cid,
            "timestamp": ev["timestamp"],
            "action": action,
            "triggers_fired": [t for t in ("T1", "T2", "T3", "T5", "RA") if t in fired],
            "chain": chain,
            "intervention_active": intervention_active,
            "risk_score": min(score, 100),
            "reasons": reasons,
            "messages": {
                "customer": messages.CUSTOMER[action],
                "staff": messages.STAFF[action],
                "family": messages.family_message(customer, action),
            },
            "money_released": action in ("allow", "warn"),
        }

    # ---------- helpers ----------

    @staticmethod
    def _recent(state, now):
        """This customer's records from the last CHAIN_WINDOW_DAYS (older ones are dropped)."""
        cutoff = now - timedelta(days=config.CHAIN_WINDOW_DAYS)
        state["records"] = [r for r in state["records"] if r["ts"] >= cutoff]
        return list(state["records"])

    @staticmethod
    def _pick_action(fired, chain, hold_active):
        """docs/DECISION_SPEC.md Step 2: first matching rule wins."""
        if not fired:
            return "allow"
        if "T5" in fired:
            return "escalate" if hold_active else "hold"
        if len(chain) >= 3:
            return "hold"
        if len(chain) == 2:
            return "pause"
        return "warn"

    @staticmethod
    def _chain_reasons(chain, recent, reasons_now):
        """One line per trigger in the chain, using the most recent event that fired it."""
        lines = []
        for t in chain:
            if t in reasons_now:
                lines.append(reasons_now[t])
                continue
            for r in reversed(recent):
                if t in r["reasons"]:
                    lines.append(r["reasons"][t])
                    break
        return lines
