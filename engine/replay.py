"""Replays every scenario through the engine and prints the week as the bank saw it.

This is the demo and the evidence in one command. It:
  1. loads data/scenarios/*.json,
  2. runs every event through the engine AND through the single-transaction baseline,
  3. prints a table of the week plus the scoreboard for the pitch,
  4. writes demo/decisions.json for the demo page.

Run from the repo root (no installs needed):
    python3 -m engine.replay
    python3 -m engine.replay --json      # machine-readable, for the API or the page
"""

import json
import sys
from pathlib import Path

from engine import config
from engine.baseline import SingleTransactionBaseline
from engine.engine import Engine
from engine.parsing import parse_timestamp

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = ROOT / "data" / "scenarios"
OUTPUT = ROOT / "demo" / "decisions.json"

STOPPED = ("pause", "hold", "escalate")  # the bank did not let the money go
BADGE = {"allow": "ALLOW", "warn": "WARN", "pause": "PAUSE", "hold": "HOLD", "escalate": "ESCALATE"}


def load_scenarios():
    """Every data/scenarios/*.json. Files starting with "_" are examples, not data.

    If the real files don't exist yet, fall back to the format example so the replay
    still shows something.
    """
    if not SCENARIOS_DIR.is_dir():
        return []
    files = sorted(p for p in SCENARIOS_DIR.glob("*.json") if not p.name.startswith("_"))
    if not files:
        example = SCENARIOS_DIR / "_format_example.json"
        files = [example] if example.exists() else []
    return [json.loads(p.read_text()) for p in files]


def replay(scenarios):
    """Run every scenario through both systems. Returns replay items in time order."""
    engine, baseline = Engine(), SingleTransactionBaseline()
    customers, events = {}, []

    for scenario in scenarios:
        customer = scenario["customer"]
        history = scenario.get("history", [])
        engine.register(customer, history)
        baseline.register(customer, history)
        customers[customer["customer_id"]] = customer
        events += scenario.get("live", [])

    # One shared timeline, the way a real day at the bank arrives.
    events.sort(key=lambda e: parse_timestamp(e["timestamp"]))

    items = []
    for event in events:
        customer = customers[event["customer_id"]]
        items.append(
            {
                "customer": {k: customer.get(k) for k in ("customer_id", "name", "age", "opted_in")},
                "event": event,
                "decision": engine.process(event),
                "baseline": baseline.process(event),
            }
        )
    return items


def describe(event):
    """One short line describing what the customer did."""
    kind = {
        "internal_transfer": lambda e: f"moved ${e['amount']:,.0f} {e.get('from_account')} -> checking",
        "cash_withdrawal": lambda e: f"withdrew ${e['amount']:,.0f} cash"
        + (f" at {e['branch_id']}" if e.get("branch_id") else ""),
        "wire": lambda e: f"wired ${e['amount']:,.0f} to {e.get('payee_name')}",
        "payment": lambda e: f"paid ${e['amount']:,.0f} to {e.get('payee_name')}",
        "deposit": lambda e: f"deposited ${e['amount']:,.0f}",
        "login": lambda e: "logged in" + (" (remote access)" if e.get("remote_access") else ""),
    }.get(event.get("type"), lambda e: e.get("type", "?"))
    return kind(event)


def scoreboard(items):
    """The numbers for the pitch, worked out from the ground-truth labels."""
    scam_ids = {i["customer"]["customer_id"] for i in items if i["event"].get("truth") == "scam"}
    innocent_ids = {i["customer"]["customer_id"] for i in items} - scam_ids

    def first_stop(cid, key):
        for i in items:
            if i["customer"]["customer_id"] == cid and i[key]["action"] in STOPPED:
                return parse_timestamp(i["event"]["timestamp"])
        return None

    rows, saved_us, saved_them, days_earlier = [], 0.0, 0.0, []
    for cid in sorted(scam_ids):
        ours, theirs = first_stop(cid, "decision"), first_stop(cid, "baseline")
        name = next(i["customer"]["name"] for i in items if i["customer"]["customer_id"] == cid)
        scam_events = [
            i for i in items
            if i["customer"]["customer_id"] == cid and i["event"].get("truth") == "scam"
        ]
        # Outflows only: money moved between a customer's own accounts never left the bank.
        leaving = [i for i in scam_events if i["event"].get("type") in config.OUTFLOW_TYPES]
        held = sum(i["event"]["amount"] for i in leaving if not i["decision"]["money_released"])
        held_base = sum(i["event"]["amount"] for i in leaving if not i["baseline"]["money_released"])
        saved_us += held
        saved_them += held_base
        if ours and theirs:
            days_earlier.append((theirs - ours).total_seconds() / 86400)
        rows.append(
            {
                "customer_id": cid, "name": name,
                "ours": ours.strftime("%b %d") if ours else "never",
                "theirs": theirs.strftime("%b %d") if theirs else "never",
                "held": held, "held_baseline": held_base,
            }
        )

    false_alarms = sorted(
        {i["customer"]["customer_id"] for i in items
         if i["customer"]["customer_id"] in innocent_ids and i["decision"]["action"] in STOPPED}
    )
    false_alarms_base = sorted(
        {i["customer"]["customer_id"] for i in items
         if i["customer"]["customer_id"] in innocent_ids and i["baseline"]["action"] in STOPPED}
    )
    return {
        "rows": rows,
        "scams": len(scam_ids),
        "scams_stopped": sum(1 for r in rows if r["ours"] != "never"),
        "scams_stopped_baseline": sum(1 for r in rows if r["theirs"] != "never"),
        "innocents": len(innocent_ids),
        "false_alarms": false_alarms,
        "false_alarms_baseline": false_alarms_base,
        "protected": saved_us,
        "protected_baseline": saved_them,
        "avg_days_earlier": sum(days_earlier) / len(days_earlier) if days_earlier else 0.0,
    }


def print_report(items, score):
    line = "=" * 108
    print(line)
    print("SENIOR SCAM SHIELD  |  replay of the week, every customer, as the bank saw it")
    print(line)
    print(f"{'WHEN':<12} {'CUSTOMER':<16} {'WHAT HAPPENED':<42} {'OURS':<9} {'RULE TODAY':<10} RISK")
    print("-" * 108)
    for i in items:
        ts = parse_timestamp(i["event"]["timestamp"])
        d, b = i["decision"], i["baseline"]
        print(
            f"{ts.strftime('%a %b %d'):<12} {i['customer']['name'][:15]:<16} "
            f"{describe(i['event'])[:41]:<42} {BADGE[d['action']]:<9} "
            f"{BADGE[b['action']]:<10} {d['risk_score']:>3}"
        )
        if d["action"] != "allow":
            for reason in d["reasons"]:
                print(f"{'':<29}   - {reason}")
            if d["messages"]["family"]:
                print(f"{'':<29}   -> family alert sent")
    print(line)
    print("SCOREBOARD")
    print("-" * 108)
    print(f"{'SCAM VICTIM':<22} {'WE STOPPED IT':<16} {'RULE TODAY':<16} {'WE HELD BACK':<16} RULE HELD BACK")
    for r in score["rows"]:
        print(
            f"{r['name'][:21]:<22} {r['ours']:<16} {r['theirs']:<16} "
            f"${r['held']:>14,.0f} ${r['held_baseline']:>14,.0f}"
        )
    print("-" * 108)
    print(f"  Scams stopped            : {score['scams_stopped']}/{score['scams']}"
          f"   (single-transaction rule: {score['scams_stopped_baseline']}/{score['scams']})")
    print(f"  Innocent customers held  : {len(score['false_alarms'])}/{score['innocents']}"
          f"   (single-transaction rule: {len(score['false_alarms_baseline'])}/{score['innocents']})")
    if score["false_alarms"]:
        print(f"    ours flagged: {', '.join(score['false_alarms'])}")
    if score["false_alarms_baseline"]:
        print(f"    rule flagged: {', '.join(score['false_alarms_baseline'])}")
    print(f"  Money kept in the bank   : ${score['protected']:,.0f}"
          f"   (single-transaction rule: ${score['protected_baseline']:,.0f})")
    if score["avg_days_earlier"]:
        print(f"  We intervene on average    {score['avg_days_earlier']:.1f} days earlier")
    print(line)


def main():
    scenarios = load_scenarios()
    if not scenarios:
        print("No scenario files found in data/scenarios/. Nothing to replay.")
        return 1
    items = replay(scenarios)
    score = scoreboard(items)

    if "--json" in sys.argv:
        print(json.dumps(items, indent=2))
        return 0

    print_report(items, score)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(items, indent=2) + "\n")
    print(f"Wrote {len(items)} decisions to {OUTPUT.relative_to(ROOT)} for the demo page.")
    print(f"Scenarios replayed: {', '.join(s.get('scenario', '?') for s in scenarios)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
