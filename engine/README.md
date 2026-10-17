# engine/ : Decision engine

**Owner:** Rinin
**Goal:** turn each Event into a Decision, exactly as described in [`docs/DECISION_SPEC.md`](../docs/DECISION_SPEC.md), using the shapes in [`docs/CONTRACT.md`](../docs/CONTRACT.md).

## Rules for this folder
- Plain Python 3.12 standard library only (no pandas, no numpy). It must run on LinuxONE (s390x) with zero installs.
- The engine must **never** read the `truth` field of an event.
- All thresholds live in one `config.py` so they can be tuned in one place.

## Suggested files
| File | What it does |
|---|---|
| `config.py` | All settings from the spec (`CHAIN_WINDOW_DAYS = 7`, `T1_MULTIPLIER = 5`, ...) |
| `parsing.py` | Normalises messy JSON: `"...Z"` timestamps, `"$9,000"` amounts, missing fields |
| `profile.py` | Builds a customer's "normal" from their history (normal transfer, normal cash, known payees) |
| `triggers.py` | Checks one event and returns which of T1, T2, T3, T5, RA fired |
| `engine.py` | `Engine` class: `register(customer, history)`, `process(event) -> decision dict`, remembers the last 7 days per customer |
| `messages.py` | Reason strings and customer / staff / family messages |
| `baseline.py` | The "single-transaction rule" used for comparison in the pitch |
| `replay.py` | Loads every file in `data/scenarios/`, runs it, prints a table, writes `demo/decisions.json` |
| `test_engine.py` | Checks the "Expected results" table at the bottom of the spec |

## Checklist
- [x] `config.py` with every setting
- [x] `profile.py`
- [x] `triggers.py` (T1, T2, T3, T5, RA + trusted payee skip)
- [x] `engine.py` (action ladder + opt-in cap + 7 day memory)
- [x] `messages.py`
- [x] Gold bar scenario gives warn, pause, hold, escalate (tested on `_format_example.json`)
- [x] All innocents never paused or held (`test_engine.py`, 16 tests)
- [ ] `replay.py` writes `demo/decisions.json`
- [ ] `baseline.py` comparison numbers for the pitch

## Run the tests
```bash
python -m unittest engine.test_engine -v   # from the repo root, no installs needed
```

## Compatibility, verified
- **Python 3.12 (the server) and 3.13**: 25 tests pass on both.
- **Standard library only**: nothing to `pip install` on LinuxONE.
- **Architecture-independent**: no `struct`, `pickle`, `ctypes` or byte-order tricks, so big-endian s390x behaves exactly like a laptop. The engine also does no file or network access.
- **Throughput**: ~30,000 decisions/sec on a laptop core. Per-customer memory is bounded by the 7-day window (about 30 records), not by total history.
- **Messy data tolerated**: a `"Z"` on some timestamps and not others, `"$9,000"` instead of `9000`, or missing optional fields won't crash the engine. The API still validates strictly, so bad input is caught at the edge.
- **Boundary**: exactly 7.0 days apart counts as linked; 7 days and a minute does not.

## Extension point for the ML layer (step 4)
`Engine(scorer=...)` takes an optional callable. When present it is called for every event and
its result is attached to the decision as `"ml"`. **The rules still decide the action**; the model
only adds a number, so turning it on cannot break the demo.

```python
from engine.engine import Engine

def model(features):          # features: 13 floats, see Engine.features()
    return {"risk": 0.87, "model": "keras-lstm"}

eng = Engine(scorer=model)    # decisions now carry decision["ml"]
```
`Engine.features()` returns the same numbers whether you are training or scoring, so use it to
build the training set too. If you later want the model to bump a borderline case up a tier, do
it explicitly in `_pick_action`, not inside the scorer.

## Interface the API team will call
```python
from engine.engine import Engine

eng = Engine()
eng.register(customer_dict, history_list)   # once per customer
decision = eng.process(event_dict)          # returns a Decision dict (see CONTRACT.md)
```
Keep these two method names stable. The API team builds against them.

## Prompt to start a Claude session
> I'm building the decision engine for Senior Scam Shield (IBM Z Datathon). Read `CLAUDE.md`, `docs/CONTRACT.md` and `docs/DECISION_SPEC.md`. Help me write `engine/config.py` and `engine/triggers.py` in plain Python 3.12 standard library only. Walk me through it step by step.
