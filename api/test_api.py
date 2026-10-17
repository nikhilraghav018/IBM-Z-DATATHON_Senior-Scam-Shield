"""API tests. Run from the repo root: python -m pytest api -q"""

import json

import pytest
from fastapi.testclient import TestClient

from api import main

EXAMPLE = json.loads((main.SCENARIOS_DIR / "_format_example.json").read_text())
CUSTOMER = EXAMPLE["customer"]
HISTORY = EXAMPLE["history"]
LIVE = EXAMPLE["live"]
ACTIONS = {"allow", "warn", "pause", "hold", "escalate"}


class FakeEngine:
    """Stands in for engine.engine.Engine: warns on every event, records what it was given."""

    def __init__(self):
        self.seen = []

    def register(self, customer, history):
        self.seen += history

    def process(self, event):
        self.seen.append(event)
        decision = main.stub_decision(event)
        return {**decision, "action": "warn"}


@pytest.fixture
def stub_client(monkeypatch):
    monkeypatch.setattr(main, "Engine", None)
    monkeypatch.setattr(main, "state", main.State())
    return TestClient(main.app)


@pytest.fixture
def engine_client(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "Engine", FakeEngine)
    monkeypatch.setattr(main, "ENGINE_MODE", "real")
    monkeypatch.setattr(main, "state", main.State())
    scenario = {**EXAMPLE, "scenario": "gold_bar"}
    (tmp_path / "gold_bar.json").write_text(json.dumps(scenario))
    monkeypatch.setattr(main, "SCENARIOS_DIR", tmp_path)
    return TestClient(main.app)


def test_health(stub_client):
    r = stub_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["arch"]
    assert r.headers["x-engine"] == "stub"


def test_cors_allows_demo_page(stub_client):
    r = stub_client.get("/health", headers={"Origin": "http://localhost:5500"})
    assert r.headers["access-control-allow-origin"] == "*"


def test_stub_replay_returns_sample_items_sorted(stub_client):
    items = stub_client.post("/demo/replay").json()
    assert len(items) == len(main.load_samples())
    times = [i["event"]["timestamp"] for i in items]
    assert times == sorted(times)
    for item in items:
        assert set(item) == {"customer", "event", "decision"}
        assert item["decision"]["action"] in ACTIONS


def test_replay_twice_gives_same_timeline(stub_client):
    stub_client.post("/demo/replay")
    stub_client.post("/demo/replay")
    timeline = stub_client.get("/customers/C1/timeline").json()
    assert [d["event_id"] for d in timeline] == ["C1-E101", "C1-E102", "C1-E103", "C1-E104"]


def test_stub_event_uses_sample_decision(stub_client):
    stub_client.post("/customers", json={"customer": CUSTOMER, "history": HISTORY})
    decision = stub_client.post("/events", json=LIVE[1]).json()
    assert decision["event_id"] == "C1-E102"
    assert decision["action"] == "pause"


def test_stub_unknown_event_is_allowed(stub_client):
    event = {**LIVE[0], "event_id": "C9-E001", "customer_id": "C9"}
    decision = stub_client.post("/events", json=event).json()
    assert decision["action"] == "allow"
    assert decision["money_released"] is True


def test_bad_event_is_rejected(stub_client):
    event = {**LIVE[0], "type": "HOLD", "amount": "$80,000"}
    del event["channel"]
    r = stub_client.post("/events", json=event)
    assert r.status_code == 422
    assert len(r.json()["detail"]) == 4


def test_bad_customer_is_rejected(stub_client):
    r = stub_client.post("/customers", json={"customer": {"customer_id": "C1"}})
    assert r.status_code == 422


def test_timeline_unknown_customer(stub_client):
    assert stub_client.get("/customers/C404/timeline").status_code == 404


def test_reset_clears_timelines(stub_client):
    stub_client.post("/demo/replay")
    assert stub_client.post("/reset").json() == {"reset": True}
    assert stub_client.get("/customers/C1/timeline").status_code == 404


def test_engine_never_sees_truth(engine_client):
    engine_client.post("/customers", json={"customer": CUSTOMER, "history": HISTORY})
    engine_client.post("/events", json=LIVE[0])
    assert main.state.engine.seen
    assert all("truth" not in e for e in main.state.engine.seen)


def test_engine_event_needs_registered_customer(engine_client):
    assert engine_client.post("/events", json=LIVE[0]).status_code == 404


def test_engine_replay_runs_scenarios(engine_client):
    r = engine_client.post("/demo/replay")
    assert r.headers["x-engine"] == "real"
    items = r.json()
    assert [i["event"]["event_id"] for i in items] == [e["event_id"] for e in LIVE]
    assert items[0]["customer"] == {k: CUSTOMER[k] for k in main.REPLAY_CUSTOMER_FIELDS}
    assert items[0]["event"]["truth"] == "scam"  # the demo page still gets the truth label
    assert all(i["decision"]["action"] == "warn" for i in items)
    assert len(engine_client.get("/customers/C1/timeline").json()) == len(LIVE)
