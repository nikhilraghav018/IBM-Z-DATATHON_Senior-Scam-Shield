# Copilot Context: Senior Scam Shield, Data Owner Tasks

Repo: https://github.com/nikhilraghav018/IBM-Z-DATATHON_Senior-Scam-Shield
Event: IBM Z Datathon 2026 (Challenge: Real-Time AI for Critical Decisions)
My role: "Shums", owner of the `data/` folder. I edit **only** files in `data/` (and later `demo/`).

## What the project does

Senior Scam Shield watches the **sequence** of a customer's money moves across days and channels (online, branch, phone, wire). It responds in tiers: **warn, pause, hold (with trusted-contact alert), escalate**. The engine (Rinin's job, `engine/`) replays my JSON files and decides an action at each event. My files are the test data, so mistakes here corrupt the engine's results and the pitch numbers.

Engine triggers: T1 unusual move, T2 risky destination (gold/crypto), T3 repeated large outflows, T5 workaround after bank intervention, RA remote-access software.
Decision rule: 1 sign = warn, 2 = pause, 3+ or a workaround = hold + family alert, workaround during a hold = escalate.

## Read these first (completed)

- `docs/CONTRACT.md`: the exact Customer and Event fields and allowed values. **Source of truth for field names.**
- `docs/SCENARIOS.md`: every story, day by day, with the expected action.
- `data/scenarios/_format_example.json`: exact file layout. Copy it for each new file.
- `CLAUDE.md`, `docs/DECISION_SPEC.md`

Do not invent field names or enum values. Take them from CONTRACT.md.

## Current progress as of 2026-10-17

Completed in the data folder:

- Created `data/make_history.py` to generate realistic normal history for a customer using a fixed seed.
- Generated and validated the following scenario files:
  - `data/scenarios/gold_bar.json` (C1)
  - `data/scenarios/grandparent.json` (C2)
  - `data/scenarios/phantom_hacker.json` (C3)
  - `data/scenarios/home_buyer.json` (C4)
- Each generated file includes a valid 60–90 day history block plus the live scam/innocent story events in the required field format.
- JSON validation was run with Python and returned `JSON_OK` for each generated file.
- No git commit or push was made.

## Deliverables

| File | Customer | Priority |
|---|---|---|
| `data/scenarios/gold_bar.json` | C1 | **First, Rinin needs it by 1 PM** |
| `data/scenarios/grandparent.json` | C2 | 2 |
| `data/scenarios/phantom_hacker.json` | C3 | 3 |
| `data/scenarios/home_buyer.json` | C4 | 4 |
| `data/scenarios/coin_collector.json` | C5 | 4 |
| `data/scenarios/car_buyer.json` | C6 | 4 |
| `data/scenarios/crypto_investor.json` | C7 | 4 |
| `data/scenarios/tax_payment.json` | C8 | 4 |
| `data/make_history.py` | all | script that generates normal history |

Each scenario file = **generated history** (60 to 90 days before Oct 19) + **hand-written live events** (the story).

## `data/make_history.py` spec

Fixed random seed. Per customer, generate:

- Monthly `deposit` (Social Security or pension)
- Weekly grocery and pharmacy `payment`s, $40 to $200
- Monthly utility `payment` (verified payee)
- A few ATM `cash_withdrawal`s, $100 to $300, at the **home branch**
- A couple of `internal_transfer`s, savings to checking, $500 to $1,500
- **C5 only:** monthly $2,000 to $4,000 payment to Heritage Coins (`gold_dealer`)
- **C7 only:** monthly $300 to $700 payment to Coinbase

## Live events (all in the week Mon Oct 19 to Sat Oct 24, 2026)

All scam victims are `opted_in: true` with a trusted contact (otherwise the engine can never reach `hold`).

### Scam 1: Gold bar (C1)
| Day | Action | Expected |
|---|---|---|
| Mon | $150,000 investment to checking (online) | warn (T1) |
| Tue | Wire $80,000 to a gold dealer never paid before | pause (T1 + T2) |
| Thu | Wire $60,000 to the same gold dealer again | hold (T5 after the pause) |
| Fri | Different branch, withdraw $40,000 cash | escalate (T5 while hold active) |

### Scam 2: Grandparent (C2)
| Day | Action | Expected |
|---|---|---|
| Mon | $9,000 cash at Branch A (normally ~$200) | warn (T1) |
| Wed | $15,000 cash at Branch B, "home repairs" | pause (T1 + T3) |
| Sat | $25,000 cash at Branch C | hold (T5 after the pause) |

### Scam 3: Phantom hacker (C3)
| Day | Action | Expected |
|---|---|---|
| Mon | Login with remote-access software running | allow (RA starts) |
| Mon | $200,000 savings to checking, same session | pause (RA + T1) |
| Tue | Wire $200,000 to new payee "Federal Reserve Safe Account" | hold (T5 after the pause) |
| Wed | Withdraw $40,000 cash at a branch (told to feed a crypto ATM) | escalate (T5 while hold active) |

### Innocent look-alikes (must NEVER be paused or held)
| Customer | Story | Why it stays clean |
|---|---|---|
| C4 Home buyer | Mon $120,000 savings to checking. Wed $118,500 wire to Collin County Title (`title_escrow`, `payee_verified: true`) | Verified payee. Only a Monday warning |
| C5 Coin collector | Tue $3,000 to Heritage Coins (`gold_dealer`), same dealer monthly in history | Trusted payee (paid 2+ times) |
| C6 Car buyer | Wed one $20,000 cash withdrawal at home branch, nothing after | One trigger only, so warn |
| C7 Crypto investor | Thu $500 to Coinbase, same as every month in history | Trusted payee, small amount |
| C8 Tax payment | Mon $30,000 savings to checking. Thu $28,000 to IRS (`government`, `payee_verified: true`) | Verified payee |

## Quality checks before every push

- [ ] Valid JSON: `python -m json.tool data/scenarios/<file>.json`
- [ ] Every event has **every** field from CONTRACT.md (`null` when unused)
- [ ] `event_id`s are unique
- [ ] Live events are in time order and within Oct 19 to 24, 2026
- [ ] Same payee always has the same `payee_id` (critical for Heritage Coins and Coinbase: trusted after 2+ payments)
- [ ] Scam victims have `opted_in: true`
- [ ] `truth` is `scam` on scam steps, `normal` everywhere else (including all innocent customers)

A small validation script (JSON validity, unique IDs, sorted live events, date range, payee_id consistency, required fields) would be worth adding as `data/validate.py`.

## Evidence for submission (later in the day)

- Screenshot: `uname -m` and `lscpu | grep -i nnpa` on the server
- Screenshot: the engine's replay table running on LinuxONE
- Screenshot: `docker ps` showing the API container
- Fill in the **Results** section of the root README: scams stopped, days earlier than the single-transaction rule, dollars protected, innocent customers held (target: 0)

## Then: demo page

After all 8 files are pushed (target ~4 PM), build the demo page per `demo/README.md`, Part 2. Kamali records it, so it must be ready by 9 PM.

## Team timeline (CDT, Oct 17)

| By | Checkpoint |
|---|---|
| 10:30 AM | Everyone has read CONTRACT.md |
| 1:00 PM | `gold_bar.json` done |
| 4:00 PM | Scenario files done, demo page starts |
| 7:00 PM | All 8 scenarios run through the engine |
| 9:00 PM | Demo page talks to the real API, Kamali records |
| Midnight | Bugs fixed, README results filled in |

## Pitch comparison (single-transaction rule)

Flags any single outflow >= $50,000, or any wire >= $25,000 to a first-time payee.
- Misses the grandparent scam completely (every withdrawal is under $50,000)
- Falsely flags the home buyer's $118,500 title wire
- Never connects the branch workaround to anything

## Git workflow

```bash
git pull origin main
git checkout -b shums

python -m json.tool data/scenarios/gold_bar.json   # validate
git status
git add data/make_history.py data/scenarios/gold_bar.json   # stage by name, never `git add .`
git commit -m "Add gold bar scenario (C1)"
git push -u origin shums
```

Then open a pull request `shums` into `main`. Rules:

1. Only edit files in `data/` (and `demo/` for the page). Changes to `docs/` get announced in team chat first.
2. Work on branch `shums`, open PRs into `main`.
3. `git pull origin main` before starting anything new.
4. **Never commit** the `.pem` key, the Jupyter token, or any password. Check `git status` before every commit.

## Suggested first prompt for Copilot

> Read `docs/CONTRACT.md`, `docs/SCENARIOS.md` and `data/scenarios/_format_example.json`. Then write `data/make_history.py` (fixed seed, spec in COPILOT_CONTEXT.md) and `data/scenarios/gold_bar.json` for customer C1. Use exactly the field names and allowed values from CONTRACT.md. After that, write `data/validate.py` to run the quality checks on every file in `data/scenarios/`.
