# Rinin: status log

**Role:** Decision engine (`engine/`)

Add a new entry at the TOP each time you finish something, then commit and push.
Keep it short. "Blocked on" is the important line: if you're stuck, say so here.

<!-- Copy this block for each new entry:
## <time>: Done: <what you finished>
Next: <what you're starting>
Blocked on: <nothing, or what you need and from whom>
-->
## 6:28 PM Sat Oct 17

**Done:**
- decisions.json regenerated from real scenarios, pushed
- Reveal label fix ("being scammed this week") confirmed in index.html
- Rebased over Nikhil's ML merge (PR #5), no conflicts
- All demo page features committed: scam reveal, day-one result line, privacy note, score explanation

**Next:**
- Retake evidence screenshot 03 against merged page (low priority)
- Available for questions from Nikhil/Kamali on engine or submission fields

**Blocked on:** nothing
## 3:50 PM: Done: merged the two demo pages into one
Shums and I had both built `demo/index.html`. Combined them rather than picking: his row layout and
always-visible messages (better for a recording, where nobody can click), my palette and the
"rule today" comparison column, plus action filters (allowed / warn / pause / hold / escalate) from
Nikhil's suggestion. It now fetches live from the LinuxONE API and falls back to `decisions.json`.
Verified against Shums's real scenarios: 3 of 3 scams interrupted versus 2 of 3 for the single
transaction rule, 0 of 5 ordinary customers stopped versus 1 of 5, $460,000 kept in the bank.
Next: ML risk score on Telum if there is time after the recording
Blocked on: nothing

## 2:55 PM: Superseded: first version of the demo page
Built the page Kamali records. One file, no frameworks. Shows the week as a bank ledger with two
verdict columns: ours and the single-transaction rule. "Play the week" reveals it a day at a time;
selecting a row opens the reasons and the customer / teller / family messages. It calls the live API
on LinuxONE first and falls back to `decisions.json` after 2.5 seconds, so it can't go blank mid-recording.
Also changed the money figure to count outflows only, since a transfer between a customer's own
accounts never left the bank. That drops it from $660k to $460k and is much harder to argue with.
Next: screenshot the replay running on LinuxONE over SSH, then the ML risk score if time allows
Blocked on: Shums's scenario files. `decisions.json` is placeholder output from docs/SCENARIOS.md until then.

## 1:25 PM: Done: replay + single-transaction baseline (step 2)
`python3 -m engine.replay` prints the whole week for every customer, what we decided vs what a
single-transaction rule would have done, and the scoreboard. It writes `demo/decisions.json` for the page.
Dry run across all 8 stories (my own stand-in data, Shums's real files will replace it):
3/3 scams stopped vs 2/3 for the single-transaction rule, 0/4 innocent customers held vs 1/4,
$660k held back vs $340k. **The grandparent scam is the one the simple rule misses completely**, so
the video should lead with it, not the gold bar one.
Next: step 3, run the replay on LinuxONE and screenshot it
Blocked on: Shums's scenario files for the real numbers

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
