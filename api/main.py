"""Senior Scam Shield API.

Wraps the decision engine (engine/engine.py) in a small web service for the demo page.
Shapes follow docs/CONTRACT.md exactly.

Until the engine exists, the API runs in "stub" mode: decisions come from
demo/sample_decisions.json so the demo page can connect early. Every response
carries an `X-Engine: real` or `X-Engine: stub` header so you can tell which mode is on.

Run locally:   uvicorn api.main:app --reload --port 8000
Run on server: uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import json
import platform
import threading
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = ROOT / "data" / "scenarios"
SAMPLE_DECISIONS = ROOT / "demo" / "sample_decisions.json"

try:
    from engine.engine import Engine
except ImportError:
    Engine = None

ENGINE_MODE = "real" if Engine else "stub"

# Allowed values from docs/CONTRACT.md section 2.
EVENT_FIELDS = (
    "event_id", "customer_id", "timestamp", "type", "channel", "amount",
    "from_account", "to_account", "payee_id", "payee_name", "payee_category",
    "payee_verified", "branch_id", "remote_access", "truth",
)
EVENT_TYPES = {"login", "internal_transfer", "cash_withdrawal", "wire", "payment", "deposit"}
CHANNELS = {"online", "branch", "phone", "atm"}
CUSTOMER_FIELDS = ("customer_id", "name", "age", "opted_in", "trusted_contact", "home_branch")
REPLAY_CUSTOMER_FIELDS = ("customer_id", "name", "age", "opted_in")

app = FastAPI(title="Senior Scam Shield API")

# The demo page runs on a laptop and calls this server, so the browser needs CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Engine"],
)


@app.middleware("http")
async def add_engine_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Engine"] = ENGINE_MODE
    return response


class State:
    """Everything the API remembers between requests. /reset makes a fresh one."""

    def __init__(self):
        self.engine = Engine() if Engine else None
        self.customers = {}  # customer_id -> Customer
        self.timelines = {}  # customer_id -> [Decision]


state = State()
# The engine keeps per-customer memory, so handle one event at a time.
lock = threading.Lock()


# ---------- helpers ----------


def check_event(event):
    """Return a list of problems with an Event dict (empty list = OK)."""
    problems = [f"missing field '{f}'" for f in EVENT_FIELDS if f not in event]
    if event.get("type") not in EVENT_TYPES:
        problems.append(f"type must be one of {sorted(EVENT_TYPES)}")
    if event.get("channel") not in CHANNELS:
        problems.append(f"channel must be one of {sorted(CHANNELS)}")
    amount = event.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        problems.append("amount must be a plain number")
    return problems


def check_customer(customer):
    return [f"missing field '{f}'" for f in CUSTOMER_FIELDS if f not in customer]


def without_truth(event):
    """The engine must never see the ground-truth label."""
    return {k: v for k, v in event.items() if k != "truth"}


def load_samples():
    with SAMPLE_DECISIONS.open() as f:
        return json.load(f)


def stub_decision(event):
    """Used until the engine exists: the sample decision for this event_id, else a plain allow."""
    for item in load_samples():
        if item["decision"]["event_id"] == event["event_id"]:
            return item["decision"]
    return {
        "event_id": event["event_id"],
        "customer_id": event["customer_id"],
        "timestamp": event["timestamp"],
        "action": "allow",
        "triggers_fired": [],
        "chain": [],
        "intervention_active": False,
        "risk_score": 0,
        "reasons": [],
        "messages": {"customer": None, "staff": None, "family": None},
        "money_released": True,
    }


def register(customer, history):
    if state.engine:
        state.engine.register(customer, [without_truth(e) for e in history])
    state.customers[customer["customer_id"]] = customer
    state.timelines.setdefault(customer["customer_id"], [])


def decide(event):
    if state.engine:
        decision = state.engine.process(without_truth(event))
    else:
        decision = stub_decision(event)
    state.timelines.setdefault(event["customer_id"], []).append(decision)
    return decision


def load_scenarios():
    """Every data/scenarios/*.json except files starting with '_' (format examples)."""
    if not SCENARIOS_DIR.is_dir():
        return []
    return [
        json.loads(path.read_text())
        for path in sorted(SCENARIOS_DIR.glob("*.json"))
        if not path.name.startswith("_")
    ]


# ---------- endpoints ----------


@app.get("/health")
def health():
    return {"status": "ok", "arch": platform.machine(), "engine": ENGINE_MODE}


@app.post("/customers")
def post_customer(body: dict = Body(...)):
    customer = body.get("customer")
    history = body.get("history", [])
    if not isinstance(customer, dict) or not isinstance(history, list):
        raise HTTPException(422, "body must be {'customer': Customer, 'history': [Event]}")
    problems = check_customer(customer)
    for event in history:
        problems += [f"history {event.get('event_id')}: {p}" for p in check_event(event)]
    if problems:
        raise HTTPException(422, problems)
    with lock:
        register(customer, history)
    return {"registered": customer["customer_id"]}


@app.post("/events")
def post_event(event: dict = Body(...)):
    problems = check_event(event)
    if problems:
        raise HTTPException(422, problems)
    with lock:
        if state.engine and event["customer_id"] not in state.customers:
            raise HTTPException(404, f"customer {event['customer_id']} not registered, POST /customers first")
        return decide(event)


@app.get("/customers/{customer_id}/timeline")
def get_timeline(customer_id: str):
    if customer_id not in state.timelines:
        raise HTTPException(404, f"no customer {customer_id}")
    return state.timelines[customer_id]


@app.post("/demo/replay")
def demo_replay():
    """Replay every scenario and return {customer, event, decision} items sorted by time."""
    global state
    with lock:
        # Fresh memory each replay so running it twice gives the same answer.
        state = State()
        scenarios = load_scenarios() if state.engine else []
        if not scenarios:
            # No engine or no scenario files yet: serve the hand-written sample replay.
            items = sorted(load_samples(), key=lambda i: i["event"]["timestamp"])
            for item in items:
                state.customers.setdefault(item["customer"]["customer_id"], item["customer"])
                state.timelines.setdefault(item["customer"]["customer_id"], []).append(item["decision"])
            return items

        customers = {}
        live = []
        for scenario in scenarios:
            customer = scenario["customer"]
            register(customer, scenario.get("history", []))
            customers[customer["customer_id"]] = {k: customer[k] for k in REPLAY_CUSTOMER_FIELDS}
            live += scenario.get("live", [])
        # Interleave all customers' events in time order, like a real day at the bank.
        live.sort(key=lambda e: e["timestamp"])
        return [
            {"customer": customers[e["customer_id"]], "event": e, "decision": decide(e)}
            for e in live
        ]


@app.post("/reset")
def reset():
    global state
    with lock:
        state = State()
    return {"reset": True}
