# Senior Scam Shield

**IBM Z Datathon 2026 · Challenge: Real-Time AI for Critical Decisions**

Bank fraud checks ask "is this really the customer?" In a senior scam the answer is yes: the victim makes every move themselves, coached by the scammer. Each step looks normal on its own. Senior Scam Shield watches the **sequence** of a customer's money moves across days and channels (online, branch, phone, wire), recognizes scam chains, and responds in tiers: warn, pause, hold with a trusted-contact alert, or escalate. It runs on IBM LinuxONE, next to the bank's data.

> One line: we catch the scam by its pattern across days, not by any single transaction, and interrupt it with a gentle, human response before the money leaves the bank.

## How it works

1. **Event in:** every transaction (transfer, wire, cash withdrawal, payment, login) is sent to the engine.
2. **Triggers:** the engine checks for warning signs: an unusual move (T1), a risky destination like gold or crypto (T2), repeated large outflows (T3), a workaround after the bank stepped in (T5), and remote-access software (RA).
3. **Chain:** warning signs from the last 7 days are linked together.
4. **Decision out:** 1 sign = warn, 2 = pause and verify, 3+ or a workaround = hold + family alert, workaround during a hold = escalate.

Full rules: [`docs/DECISION_SPEC.md`](docs/DECISION_SPEC.md)

## Scenarios we demo

| Scam | Real-world basis |
|---|---|
| Gold bar (Frisco) | Collin County gold bar scam |
| Grandparent | Courier cash pickups across multiple branches |
| Phantom hacker | FBI-reported tech support / fake bank / fake government chain |

Plus five innocent look-alikes (home buyer, coin collector, car buyer, crypto investor, tax payment) that must **never** be held. Details: [`docs/SCENARIOS.md`](docs/SCENARIOS.md)

## Repo layout

| Folder | What lives there | Owner |
|---|---|---|
| `docs/` | Shared contract, decision spec, scenarios. **Read before coding** | everyone |
| `engine/` | The decision engine (plain Python, no dependencies) | Rinin |
| `api/` | FastAPI service + Docker, deployed on LinuxONE | Nikhil |
| `data/` | Scenario JSON files + evidence screenshots | Shums |
| `demo/` | Pitch video + single-page demo (HTML + JS) | Kamali (video), Shums (page) |

Each folder has its own `README.md` with a checklist and a ready-made prompt for starting a Claude session.

## Team plan for Oct 17 (all times CDT)

| By | Checkpoint |
|---|---|
| 10:30 AM | Everyone has read `docs/CONTRACT.md` and agrees on the JSON shapes |
| 1:00 PM | `data/scenarios/gold_bar.json` done. Video time limit confirmed + script draft |
| 4:00 PM | Engine handles gold bar correctly. API `/health` running on LinuxONE. Scenario files done, Shums starts the demo page. **If anything is stuck, cut scope now** |
| 7:00 PM | All 8 scenarios run through the engine. API calls the engine |
| 9:00 PM | Demo page talks to the real API on LinuxONE. Kamali records the demo segment |
| Midnight | Bugs fixed, README results filled in, video mostly edited. Morning = final cut + submit |

## Working rules

1. **Only edit files in your own folder.** Changes to `docs/` get announced in the team chat first.
2. Work on a branch named after you (`git checkout -b rinin`), push it, and open a pull request into `main`.
3. Before starting anything new: `git pull origin main`.
4. **Never commit** the `.pem` key, the Jupyter token, or any password. `.gitignore` blocks the common ones, but check `git status` before every commit.

## Running it (filled in as pieces land)

```bash
# Engine replay (prints the decision table, writes demo/decisions.json)
python3 -m engine.replay

# API (on LinuxONE)
sudo docker build -t scamshield .
sudo docker run -d -p 8000:8000 --name scamshield scamshield
curl http://localhost:8000/health
```

## Results

_To be filled in from the replay on LinuxONE: scams stopped, days earlier than the single-transaction rule, dollars protected, innocent customers held (target: 0)._

## Built on IBM LinuxONE

- Architecture `s390x`, IBM z17 with the Telum on-chip AI accelerator (`nnpa` flag confirmed)
- Ubuntu 24.04 datathon image, Python 3.12, Docker

## Future enhancements

- Neural sequence model scoring the chain, accelerated on Telum
- IBM Granite writing the plain-language explanations
- Sharing confirmed scam patterns with consumer protection agencies (FTC, CFPB)
