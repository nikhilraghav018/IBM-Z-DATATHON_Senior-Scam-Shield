# data/ : Scenario data + evidence

**Owner:** Shums
**Goal:** write the 3 scam stories and 5 innocent stories as JSON files the engine can replay, then collect the screenshots and README content the judges need.

Read first:
- [`docs/SCENARIOS.md`](../docs/SCENARIOS.md): every story, day by day, with the expected action
- [`docs/CONTRACT.md`](../docs/CONTRACT.md): the exact Customer and Event fields and allowed values

## What to produce
One file per story in `data/scenarios/`:

| File | Customer | Priority |
|---|---|---|
| `gold_bar.json` | C1 | **First. Rinin needs it by 1 PM to test the engine** |
| `grandparent.json` | C2 | 2 |
| `phantom_hacker.json` | C3 | 3 |
| `home_buyer.json` | C4 | 4 |
| `coin_collector.json` | C5 | 4 |
| `car_buyer.json` | C6 | 4 |
| `crypto_investor.json` | C7 | 4 |
| `tax_payment.json` | C8 | 4 |

`scenarios/_format_example.json` shows the exact layout with a few events. Copy it for each new file.

## Tip: generate the history, hand-write the story
Typing 90 days of grocery trips by hand is slow and error-prone. Write a small script `data/make_history.py` that produces normal history for a customer (weekly groceries, monthly deposit, a few small ATM withdrawals, see "Normal history" in SCENARIOS.md) with a fixed random seed. Then hand-write only the `live` events, because those are the story the judges see.

## Quality checks before you push a file
- [ ] Valid JSON (paste it into any JSON validator, or run `python -m json.tool data/scenarios/gold_bar.json`)
- [ ] Every event has every field from CONTRACT.md (use `null` when not used)
- [ ] `event_id`s are unique
- [ ] Live events are in time order and in the week Oct 19 to 24, 2026
- [ ] The same payee always has the same `payee_id`
- [ ] Scam victims have `opted_in: true`
- [ ] `truth` is `scam` on scam steps, `normal` everywhere else

## Evidence for the submission (later in the day)
- [ ] Screenshot: `uname -m` and `lscpu | grep -i nnpa` on the server
- [ ] Screenshot: the engine's replay table running on LinuxONE
- [ ] Screenshot: `docker ps` showing the API container
- [ ] Fill in the "Results" section of the root README with the replay numbers

## After the scenario files: build the demo page
Once all 8 files are pushed (target ~4 PM), you build the demo page that Kamali records for the video. Instructions: `demo/README.md`, Part 2. It needs to be ready to record by 9 PM.

## Prompt to start a Claude session
> I'm working on the scenario data for Senior Scam Shield (IBM Z Datathon). Read `CLAUDE.md`, `docs/CONTRACT.md`, `docs/SCENARIOS.md` and `data/scenarios/_format_example.json`. Help me write `data/make_history.py` and then `data/scenarios/gold_bar.json`, step by step.
