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


if __name__ == "__main__":
    unittest.main()
