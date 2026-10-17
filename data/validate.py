#!/usr/bin/env python3
"""Validate all scenario JSON files in data/scenarios.

This is a lightweight quality gate for the data/ folder. It checks:
- valid JSON syntax
- required top-level structure
- required Event and Customer fields
- unique event IDs
- date range and time ordering for live events
- payee consistency across history/live events
- scam/normal truth values
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

ROOT = Path(__file__).resolve().parent
SCENARIO_DIR = ROOT / "scenarios"

REQUIRED_CUSTOMER_KEYS = {
    "customer_id",
    "name",
    "age",
    "opted_in",
    "trusted_contact",
    "home_branch",
}

REQUIRED_EVENT_KEYS = {
    "event_id",
    "customer_id",
    "timestamp",
    "type",
    "channel",
    "amount",
    "from_account",
    "to_account",
    "payee_id",
    "payee_name",
    "payee_category",
    "payee_verified",
    "branch_id",
    "remote_access",
    "truth",
}

ALLOWED_TYPES = {
    "login",
    "internal_transfer",
    "cash_withdrawal",
    "wire",
    "payment",
    "deposit",
}

ALLOWED_CHANNELS = {"online", "branch", "phone", "atm"}
ALLOWED_TRUTH = {"scam", "normal"}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def assert_keys(obj: Dict[str, Any], required: Set[str], label: str) -> None:
    missing = sorted(required - set(obj.keys()))
    if missing:
        raise ValueError(f"{label} missing required keys: {missing}")


def parse_iso(ts: str) -> str:
    try:
        # Accept ISO 8601 without timezone, as required by the contract.
        if ts.endswith("Z"):
            raise ValueError("timezone 'Z' is not allowed for this project")
        from datetime import datetime

        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        return ts
    except ValueError as exc:  # pragma: no cover - exercised by runtime checks
        raise ValueError(f"Invalid timestamp '{ts}': expected ISO format YYYY-MM-DDTHH:MM:SS") from exc


def validate_customer(customer: Dict[str, Any], scenario_name: str) -> None:
    assert_keys(customer, REQUIRED_CUSTOMER_KEYS, f"{scenario_name}.customer")
    if not isinstance(customer["customer_id"], str):
        raise ValueError(f"{scenario_name}.customer.customer_id must be a string")
    if not isinstance(customer["age"], int):
        raise ValueError(f"{scenario_name}.customer.age must be an integer")
    if not isinstance(customer["opted_in"], bool):
        raise ValueError(f"{scenario_name}.customer.opted_in must be a boolean")


def validate_event(event: Dict[str, Any], scenario_name: str, *, allow_scam_truth: bool) -> None:
    assert_keys(event, REQUIRED_EVENT_KEYS, f"{scenario_name} event {event.get('event_id', '<unknown>')}")

    if event["type"] not in ALLOWED_TYPES:
        raise ValueError(f"{scenario_name}: unsupported event type '{event['type']}'")
    if event["channel"] not in ALLOWED_CHANNELS:
        raise ValueError(f"{scenario_name}: unsupported channel '{event['channel']}'")
    if event["truth"] not in ALLOWED_TRUTH:
        raise ValueError(f"{scenario_name}: unsupported truth '{event['truth']}'")
    if allow_scam_truth and event["truth"] == "scam":
        pass
    if event["type"] == "cash_withdrawal" and event["branch_id"] is None:
        raise ValueError(f"{scenario_name}: cash_withdrawal requires branch_id")
    if event["type"] == "login" and event["amount"] != 0:
        raise ValueError(f"{scenario_name}: login amount must be 0")

    parse_iso(event["timestamp"])


def validate_history_and_live(scenario_name: str, customer_id: str, history: List[Dict[str, Any]], live: List[Dict[str, Any]]) -> None:
    seen: Set[str] = set()
    for seq_name, seq in [("history", history), ("live", live)]:
        for event in seq:
            validate_event(event, scenario_name, allow_scam_truth=True)
            if event["event_id"] in seen:
                raise ValueError(f"{scenario_name}: duplicate event_id '{event['event_id']}'")
            seen.add(event["event_id"])
            if event["customer_id"] != customer_id:
                raise ValueError(f"{scenario_name}: event {event['event_id']} customer_id mismatch")
            if seq_name == "history" and event["truth"] != "normal":
                raise ValueError(f"{scenario_name}: history event {event['event_id']} must have truth='normal'")
            if seq_name == "live" and event["truth"] not in {"scam", "normal"}:
                raise ValueError(f"{scenario_name}: live event {event['event_id']} has invalid truth '{event['truth']}'")

    if not live:
        raise ValueError(f"{scenario_name}: live events list is empty")

    timestamps = [event["timestamp"] for event in live]
    ordered = sorted(timestamps)
    if timestamps != ordered:
        raise ValueError(f"{scenario_name}: live events are not in chronological order")

    for ts in timestamps:
        dt = parse_iso(ts)
        if dt < "2026-10-19T00:00:00" or dt > "2026-10-24T23:59:59":
            raise ValueError(f"{scenario_name}: live event timestamp out of story range: {ts}")

    payee_map: Dict[str, Tuple[str, str, bool]] = {}
    for event in history + live:
        payee_id = event.get("payee_id")
        if payee_id is None:
            continue
        payee_name = event.get("payee_name")
        payee_category = event.get("payee_category")
        payee_verified = bool(event.get("payee_verified"))
        key = (payee_id, payee_name, payee_category, payee_verified)
        if payee_id in payee_map and payee_map[payee_id] != key:
            raise ValueError(
                f"{scenario_name}: payee_id '{payee_id}' is inconsistent across events"
            )
        payee_map[payee_id] = key


def validate_scenario(path: Path) -> None:
    if path.name.startswith("_"):
        return

    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: root JSON value must be an object")

    for key in ("scenario", "description", "customer", "history", "live"):
        if key not in data:
            raise ValueError(f"{path.name}: missing top-level field '{key}'")

    scenario_name = data["scenario"]
    customer = data["customer"]
    history = data["history"]
    live = data["live"]

    if not isinstance(history, list) or not isinstance(live, list):
        raise ValueError(f"{path.name}: history and live must be lists")

    validate_customer(customer, scenario_name)

    if customer["customer_id"] != data.get("customer", {}).get("customer_id"):
        raise ValueError(f"{path.name}: customer_id mismatch")

    for i, event in enumerate(history):
        if not isinstance(event, dict):
            raise ValueError(f"{path.name}: history entry {i} is not an object")
    for i, event in enumerate(live):
        if not isinstance(event, dict):
            raise ValueError(f"{path.name}: live entry {i} is not an object")

    validate_history_and_live(scenario_name, customer["customer_id"], history, live)

    if customer["opted_in"] is True:
        # Scam victims are expected to have a trusted contact. Innocent stories may still be opted_in true.
        if customer.get("trusted_contact") is None:
            raise ValueError(f"{path.name}: customer opted_in=true but trusted_contact is null")

    for event in live:
        if event["truth"] == "scam" and customer["opted_in"] is not True:
            raise ValueError(f"{path.name}: scam event found for customer not opted_in")


def main() -> None:
    scenario_files = sorted(SCENARIO_DIR.glob("*.json"))
    scenario_files = [p for p in scenario_files if not p.name.startswith("_")]

    if not scenario_files:
        raise SystemExit(f"No scenario JSON files found in {SCENARIO_DIR}")

    errors: List[str] = []
    for path in scenario_files:
        try:
            validate_scenario(path)
        except Exception as exc:  # broad to keep the script simple and user-friendly
            errors.append(f"{path.name}: {exc}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        raise SystemExit(1)

    print(f"Validated {len(scenario_files)} scenario files in {SCENARIO_DIR}")


if __name__ == "__main__":
    main()
