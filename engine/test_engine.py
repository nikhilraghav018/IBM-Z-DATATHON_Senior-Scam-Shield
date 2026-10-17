"""Tests for the decision engine: the "Expected results" table in docs/DECISION_SPEC.md.

Run from the repo root (no installs needed):
    python -m unittest engine.test_engine -v
or, if pytest is installed:
    python -m pytest engine -q
"""

import json
import unittest
from pathlib import Path

from engine.engine import Engine

ROOT = Path(__file__).resolve().parent.parent


def ev(cid, n, ts, type_, amount, truth="normal", channel="online", from_account="checking",
       to_account=None, payee_id=None, payee_name=None, category=None, verified=False,
       branch=None, remote=False):
    """Build a full Event with every CONTRACT.md field."""
    return {
        "event_id": f"{cid}-E{n:03d}", "customer_id": cid, "timestamp": ts, "type": type_,
        "channel": channel, "amount": amount, "from_account": from_account,
        "to_account": to_account, "payee_id": payee_id, "payee_name": payee_name,
        "payee_category": category, "payee_verified": verified, "branch_id": branch,
        "remote_access": remote, "truth": truth,
    }


def customer(cid, name, opted_in=True):
    return {
        "customer_id": cid, "name": name, "age": 75, "opted_in": opted_in,
        "trusted_contact": {"name": "Sam Lee", "relation": "son", "phone": "+1-214-555-0100"},
        "home_branch": "BR-HOME",
    }


def history(cid, extra=()):
    """Normal life: small ATM withdrawals, small transfers, groceries, plus any extra events."""
    h = [
        ev(cid, 901, "2026-08-05T10:00:00", "cash_withdrawal", 200, channel="atm", branch="BR-HOME"),
        ev(cid, 902, "2026-08-20T10:00:00", "internal_transfer", 1000, from_account="savings",
           to_account="checking"),
        ev(cid, 903, "2026-09-02T12:00:00", "payment", 85, payee_id="P-KRG", payee_name="Kroger",
           category="grocery"),
        ev(cid, 904, "2026-09-15T10:00:00", "cash_withdrawal", 250, channel="atm", branch="BR-HOME"),
    ]
    return h + list(extra)


def run(cust, hist, live):
    eng = Engine()
    eng.register(cust, hist)
    return [eng.process(e) for e in live]


def actions(decisions):
    return [d["action"] for d in decisions]


class GoldBar(unittest.TestCase):
    def setUp(self):
        self.s = json.loads((ROOT / "data/scenarios/_format_example.json").read_text())

    def test_warn_pause_hold_escalate(self):
        d = run(self.s["customer"], self.s["history"], self.s["live"])
        self.assertEqual(actions(d), ["warn", "pause", "hold", "escalate"])
        self.assertEqual(d[1]["chain"], ["T1", "T2"])
        self.assertIn("T5", d[2]["triggers_fired"])
        self.assertTrue(d[3]["intervention_active"])

    def test_family_alert_only_on_hold_and_escalate(self):
        d = run(self.s["customer"], self.s["history"], self.s["live"])
        self.assertEqual([x["messages"]["family"] is not None for x in d], [False, False, True, True])
        for x in d:
            fam = x["messages"]["family"] or ""
            self.assertNotIn("$", fam)  # never amounts in the family message

    def test_money_released_only_for_allow_and_warn(self):
        d = run(self.s["customer"], self.s["history"], self.s["live"])
        self.assertEqual([x["money_released"] for x in d], [True, False, False, False])

    def test_not_opted_in_caps_at_pause(self):
        cust = dict(self.s["customer"], opted_in=False)
        d = run(cust, self.s["history"], self.s["live"])
        self.assertEqual(actions(d), ["warn", "pause", "pause", "pause"])
        self.assertTrue(all(x["messages"]["family"] is None for x in d))


class Grandparent(unittest.TestCase):
    def test_reaches_hold_by_third_branch(self):
        c = "C2"
        live = [
            ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000, "scam", "branch", branch="BR-A"),
            ev(c, 2, "2026-10-21T10:00:00", "cash_withdrawal", 15000, "scam", "branch", branch="BR-B"),
            ev(c, 3, "2026-10-24T10:00:00", "cash_withdrawal", 25000, "scam", "branch", branch="BR-C"),
        ]
        d = run(customer(c, "Betty Ruiz"), history(c), live)
        self.assertEqual(actions(d), ["warn", "pause", "hold"])
        self.assertEqual(d[1]["chain"], ["T1", "T3"])


class PhantomHacker(unittest.TestCase):
    def test_pause_then_hold_then_escalate(self):
        c = "C3"
        live = [
            ev(c, 1, "2026-10-19T09:00:00", "login", 0, "scam", remote=True),
            ev(c, 2, "2026-10-19T09:10:00", "internal_transfer", 200000, "scam",
               from_account="savings", to_account="checking"),
            ev(c, 3, "2026-10-20T11:00:00", "wire", 200000, "scam", payee_id="P-SAFE",
               payee_name="Federal Reserve Safe Account", category="unknown"),
            ev(c, 4, "2026-10-21T14:00:00", "cash_withdrawal", 40000, "scam", "branch", branch="BR-X"),
        ]
        d = run(customer(c, "Harold Kim"), history(c), live)
        self.assertEqual(actions(d), ["allow", "pause", "hold", "escalate"])
        self.assertEqual(d[1]["chain"], ["T1", "RA"])


class Innocents(unittest.TestCase):
    """None of these may ever be paused, held or escalated."""

    def assert_never_stopped(self, decisions):
        for d in decisions:
            self.assertIn(d["action"], ("allow", "warn"), d)

    def test_home_buyer(self):
        c = "C4"
        live = [
            ev(c, 1, "2026-10-19T13:30:00", "internal_transfer", 120000, from_account="savings",
               to_account="checking"),
            ev(c, 2, "2026-10-21T09:45:00", "wire", 118500, payee_id="P-CCT",
               payee_name="Collin County Title", category="title_escrow", verified=True),
        ]
        d = run(customer(c, "David Chen"), history(c), live)
        self.assertEqual(actions(d), ["warn", "allow"])
        self.assertEqual(d[1]["reasons"], ["Verified payee (Collin County Title)"])

    def test_coin_collector(self):
        c = "C5"
        past = [ev(c, 910 + i, f"2026-0{7 + i}-10T15:00:00", "payment", 3000, payee_id="P-HCO",
                   payee_name="Heritage Coins", category="gold_dealer") for i in range(3)]
        live = [ev(c, 1, "2026-10-20T15:00:00", "payment", 3000, payee_id="P-HCO",
                   payee_name="Heritage Coins", category="gold_dealer")]
        d = run(customer(c, "Robert Alvarez"), history(c, past), live)
        self.assertEqual(actions(d), ["allow"])

    def test_car_buyer_not_opted_in(self):
        c = "C6"
        live = [ev(c, 1, "2026-10-21T12:10:00", "cash_withdrawal", 20000, channel="branch",
                   branch="BR-HOME")]
        d = run(customer(c, "Linda Park", opted_in=False), history(c), live)
        self.assertEqual(actions(d), ["warn"])

    def test_crypto_investor(self):
        c = "C7"
        past = [ev(c, 910 + i, f"2026-0{7 + i}-01T09:00:00", "payment", 500, payee_id="P-CB",
                   payee_name="Coinbase", category="crypto_exchange") for i in range(3)]
        live = [ev(c, 1, "2026-10-22T09:00:00", "payment", 500, payee_id="P-CB",
                   payee_name="Coinbase", category="crypto_exchange")]
        d = run(customer(c, "Ana Gomez"), history(c, past), live)
        self.assertEqual(actions(d), ["allow"])

    def test_tax_payment(self):
        c = "C8"
        live = [
            ev(c, 1, "2026-10-19T10:00:00", "internal_transfer", 30000, from_account="savings",
               to_account="checking"),
            ev(c, 2, "2026-10-22T10:00:00", "payment", 28000, payee_id="P-IRS", payee_name="IRS",
               category="government", verified=True),
        ]
        d = run(customer(c, "Frank Moore"), history(c), live)
        self.assertEqual(actions(d), ["warn", "allow"])


class Rules(unittest.TestCase):
    def test_chain_forgets_after_7_days(self):
        c = "C9"
        live = [
            ev(c, 1, "2026-10-01T10:00:00", "internal_transfer", 150000, from_account="investment",
               to_account="checking"),
            ev(c, 2, "2026-10-10T10:00:00", "wire", 80000, payee_id="P-LSB",
               payee_name="Lone Star Bullion", category="gold_dealer"),
        ]
        d = run(customer(c, "Old Chain"), history(c), live)
        self.assertEqual(actions(d), ["warn", "warn"])  # 9 days apart: not linked

    def test_engine_ignores_truth_and_does_not_change_input(self):
        c = "C10"
        e1 = ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000, "scam", "branch", branch="BR-A")
        e2 = dict(e1, truth="normal")
        before = dict(e1)
        a = run(customer(c, "Truth Test"), history(c), [e1])
        b = run(customer(c, "Truth Test"), history(c), [e2])
        self.assertEqual(a, b)
        self.assertEqual(e1, before)

    def test_small_amounts_never_fire(self):
        c = "C11"
        live = [ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 1200, channel="atm", branch="BR-HOME")]
        d = run(customer(c, "Small Spender"), history(c), live)
        self.assertEqual(actions(d), ["allow"])  # 6x normal but under the $5,000 floor

    def test_unregistered_customer_raises(self):
        with self.assertRaises(KeyError):
            Engine().process(ev("NOPE", 1, "2026-10-19T10:00:00", "login", 0))

    def test_decision_has_every_contract_field(self):
        c = "C12"
        d = run(customer(c, "Shape Test"), history(c),
                [ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000, channel="branch", branch="B")])[0]
        self.assertEqual(
            set(d),
            {"event_id", "customer_id", "timestamp", "action", "triggers_fired", "chain",
             "intervention_active", "risk_score", "reasons", "messages", "money_released"},
        )
        self.assertEqual(set(d["messages"]), {"customer", "staff", "family"})


class Compatibility(unittest.TestCase):
    """Guards the contracts other people's code depends on. Don't delete these.

    They cover the two things most likely to break tonight: hand-written scenario
    files with slightly-off JSON, and the ML layer being bolted on in step 4.
    """

    def test_timestamps_with_and_without_timezone_mix(self):
        """Shums may write "...Z" on some events and not others. Must not crash."""
        c = "X1"
        live = [
            ev(c, 1, "2026-10-19T10:00:00Z", "cash_withdrawal", 9000, channel="branch", branch="A"),
            ev(c, 2, "2026-10-21T10:00:00", "cash_withdrawal", 15000, channel="branch", branch="B"),
        ]
        self.assertEqual(actions(run(customer(c, "Mixed TZ"), history(c), live)), ["warn", "pause"])

    def test_messy_amounts_are_accepted(self):
        """"$9,000" or null instead of 9000 should still behave sensibly."""
        c = "X2"
        live = [
            ev(c, 1, "2026-10-19T10:00:00", "login", None),
            ev(c, 2, "2026-10-19T10:05:00", "cash_withdrawal", "$9,000", channel="branch", branch="A"),
        ]
        self.assertEqual(actions(run(customer(c, "Messy"), history(c), live)), ["allow", "warn"])

    def test_event_missing_optional_fields(self):
        c = "X3"
        live = [{"event_id": "X3-E1", "customer_id": c, "timestamp": "2026-10-19T10:00:00",
                 "type": "cash_withdrawal", "channel": "branch", "amount": 9000}]
        self.assertEqual(actions(run(customer(c, "Sparse"), history(c), live)), ["warn"])

    def test_seven_day_boundary_is_inclusive(self):
        """Exactly 7 days apart still counts as linked; 7 days and a minute does not."""
        c = "X4"
        pair = lambda second: [
            ev(c, 1, "2026-10-19T11:00:00", "cash_withdrawal", 9000, channel="branch", branch="A"),
            ev(c, 2, second, "cash_withdrawal", 15000, channel="branch", branch="B"),
        ]
        self.assertEqual(actions(run(customer(c, "Edge"), history(c), pair("2026-10-26T11:00:00"))),
                         ["warn", "pause"])
        self.assertEqual(actions(run(customer(c, "Edge"), history(c), pair("2026-10-26T11:01:00"))),
                         ["warn", "warn"])

    def test_engines_do_not_share_state(self):
        """api/main.py builds a fresh Engine on /reset and on every /demo/replay."""
        c = "X5"
        first = ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000, channel="branch", branch="A")
        second = ev(c, 2, "2026-10-20T10:00:00", "cash_withdrawal", 15000, channel="branch", branch="B")
        warm = Engine(); warm.register(customer(c, "Shared"), history(c))
        warm.process(first); warm.process(second)
        cold = Engine(); cold.register(customer(c, "Shared"), history(c))
        self.assertEqual(cold.process(second)["action"], "warn")

    def test_interleaved_customers_stay_separate(self):
        """/demo/replay feeds all customers' events into one Engine in time order."""
        eng = Engine()
        for cid in ("X6", "X7"):
            eng.register(customer(cid, cid), history(cid))
        seq = [
            ev("X6", 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000, channel="branch", branch="A"),
            ev("X7", 1, "2026-10-19T11:00:00", "cash_withdrawal", 9000, channel="branch", branch="A"),
            ev("X6", 2, "2026-10-20T10:00:00", "cash_withdrawal", 15000, channel="branch", branch="B"),
        ]
        self.assertEqual([eng.process(e)["action"] for e in seq], ["warn", "warn", "pause"])

    def test_scorer_hook_adds_ml_without_changing_the_action(self):
        """Step 4 plugs a model in here. The rules must still decide the action."""
        c = "X8"
        seen = {}

        def model(features):
            seen.update(features)
            return {"risk": 0.9, "model": "test"}

        live = [ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000, channel="branch", branch="A")]
        plain = run(customer(c, "NoML"), history(c), live)[0]
        eng = Engine(scorer=model)
        eng.register(customer(c, "WithML"), history(c))
        scored = eng.process(live[0])
        self.assertNotIn("ml", plain)
        self.assertEqual(scored["ml"], {"risk": 0.9, "model": "test"})
        self.assertEqual(scored["action"], plain["action"])
        self.assertTrue(seen and all(isinstance(v, float) for v in seen.values()))

    def test_decision_matches_contract_even_with_scorer(self):
        """The demo page and API must keep working when the ML layer is switched on."""
        c = "X9"
        eng = Engine(scorer=lambda f: {"risk": 0.1})
        eng.register(customer(c, "Shape"), history(c))
        d = eng.process(ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000,
                           channel="branch", branch="A"))
        required = {"event_id", "customer_id", "timestamp", "action", "triggers_fired", "chain",
                    "intervention_active", "risk_score", "reasons", "messages", "money_released"}
        self.assertTrue(required <= set(d))
        self.assertIn(d["action"], {"allow", "warn", "pause", "hold", "escalate"})

    def test_internal_fields_do_not_leak_into_decisions(self):
        """`_ts` is internal bookkeeping; it must never reach the API or the demo page."""
        c = "X10"
        d = run(customer(c, "Clean"), history(c),
                [ev(c, 1, "2026-10-19T10:00:00", "cash_withdrawal", 9000, channel="branch", branch="A")])[0]
        self.assertFalse([k for k in d if k.startswith("_")])
        json.dumps(d)  # must be JSON-serialisable for FastAPI


if __name__ == "__main__":
    unittest.main()
