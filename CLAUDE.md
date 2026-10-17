# Context for Claude sessions working in this repo

## Project
Senior Scam Shield, a team entry for the IBM Z Datathon 2026 (24-hour event, due the morning of Oct 18, 2026 CDT).
A decision engine inside a bank that watches each customer's sequence of money moves over 7 days and decides allow / warn / pause / hold / escalate to interrupt scams targeting seniors.

## Read these first
1. `docs/CONTRACT.md`: the exact JSON shapes (Customer, Event, Decision, Scenario file, Replay item). **Source of truth. Do not invent or rename fields.**
2. `docs/DECISION_SPEC.md`: the trigger rules (T1, T2, T3, T5, RA) and the action ladder.
3. `docs/SCENARIOS.md`: the 3 scam stories + 5 innocent stories and the expected action for each step.
4. The `README.md` in the folder the user is working in.

## Hard constraints
- Backend runs on **IBM LinuxONE (s390x architecture), Ubuntu 24.04, Python 3.12, 7.8 GB RAM, no swap**. Avoid packages without s390x wheels (e.g. Streamlit/pyarrow). Prefer the Python standard library.
- `engine/` uses the Python standard library only.
- The engine must never read the `truth` field of an event (it's ground truth for scoring).
- Action names are lowercase exactly: `allow`, `warn`, `pause`, `hold`, `escalate`.
- Money is a plain number in US dollars. Timestamps are ISO 8601 without timezone.
- Never put SSH keys, tokens or passwords in the repo.

## Team and folders
| Folder | Owner | Notes |
|---|---|---|
| `engine/` | Rinin | Decision logic |
| `api/` | Nikhil | FastAPI + Docker on LinuxONE, CORS, integration |
| `data/` | Shums | Scenario JSON + evidence screenshots, then the demo page |
| `demo/` | Kamali (pitch video), Shums (demo page) | Video script/slides/recording; page is a single `index.html`, plain HTML/CSS/JS, no frameworks |

Each person should only change files in their own folder.

## Status log
Each person keeps `status/<name>.md` (rinin, nikhil, shums, kamali). **Whenever the user finishes a task, remind them to add an entry at the top of their own status file (Done / Next / Blocked on) and to commit and push it together with their work.** If they say they are stuck, suggest writing it under "Blocked on" and pushing.
 Explain things step by step and keep solutions simple: it's a 24-hour build, so the simplest working solution wins.

## Time pressure
Prefer the simplest thing that works and can be demoed. Neural networks and IBM Granite are listed as future enhancements, not part of today's build, unless the team says otherwise.
