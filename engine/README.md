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
| `profile.py` | Builds a customer's "normal" from their history (normal transfer, normal cash, known payees) |
| `triggers.py` | Checks one event and returns which of T1, T2, T3, T5, RA fired |
| `engine.py` | `Engine` class: `register(customer, history)`, `process(event) -> decision dict`, remembers the last 7 days per customer |
| `messages.py` | Reason strings and customer / staff / family messages |
| `baseline.py` | The "single-transaction rule" used for comparison in the pitch |
| `replay.py` | Loads every file in `data/scenarios/`, runs it, prints a table, writes `demo/decisions.json` |
| `test_engine.py` | Checks the "Expected results" table at the bottom of the spec |

## Checklist
- [ ] `config.py` with every setting
- [ ] `profile.py`
- [ ] `triggers.py` (T1, T2, T3, T5, RA + trusted payee skip)
- [ ] `engine.py` (action ladder + opt-in cap + 7 day memory)
- [ ] `messages.py`
- [ ] Gold bar scenario gives warn, pause, hold, escalate (needs `data/scenarios/gold_bar.json`)
- [ ] All innocents never paused or held
- [ ] `replay.py` writes `demo/decisions.json`
- [ ] `baseline.py` comparison numbers for the pitch

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
