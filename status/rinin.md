# Rinin: status log

**Role:** Decision engine (`engine/`)

Add a new entry at the TOP each time you finish something, then commit and push.
Keep it short. "Blocked on" is the important line: if you're stuck, say so here.

<!-- Copy this block for each new entry:
## <time>: Done: <what you finished>
Next: <what you're starting>
Blocked on: <nothing, or what you need and from whom>
-->

## 1:05 PM: Done: compatibility pass on the engine
Fixed two crashes that hand-written scenario files would have caused: mixed "Z"/plain timestamps, and amounts written as strings like "$9,000". Added `engine/parsing.py`, plus an `Engine(scorer=...)` hook so the step-4 ML layer attaches to decisions without touching the rules. 25 tests now, passing on Python 3.12 and 3.13. Verified end to end against Nikhil's API in real mode: replay is deterministic, customers stay separate, /reset works.
Next: replay.py + single-transaction baseline (step 2)
Blocked on: Nikhil: `api/test_api.py::test_health` fails now the engine exists; the `stub_client` fixture needs `monkeypatch.setattr(main, "ENGINE_MODE", "stub")`. Shums: real scenario files in `data/scenarios/`.

## 12:55 PM: Done: basic engine (step 1)
`engine/` has config, profile, triggers, messages, engine + 16 passing tests. Gold bar gives warn, pause, hold, escalate; grandparent and phantom hacker reach hold; all 5 innocents stay at allow/warn. The API switches to real mode automatically now that `engine/engine.py` exists.
Next: replay.py + single-transaction baseline (step 2)
Blocked on: Nikhil: `api/test_api.py` `stub_client` fixture needs `monkeypatch.setattr(main, "ENGINE_MODE", "stub")`, otherwise test_health fails now that the engine exists. Shums: real scenario files in `data/scenarios/`.

## 12:30 PM: Starting
Next: Basic engine: config, profile, triggers, action ladder, messages. Target: engine + replay working by 4:30 PM
Blocked on: nothing
