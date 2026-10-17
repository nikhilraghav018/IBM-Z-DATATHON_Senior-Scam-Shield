# Data Folder Usage and Integration Guide

This guide explains how to use the data artifacts created for Senior Scam Shield and how they integrate with the rest of the repo.

## Purpose
The data folder owns the scenario test set for the project. These files define the customer histories and live scam/normal events that the engine replays to generate decisions.

## What is in this folder

### Core scripts
- data/make_history.py
  - Generates realistic normal customer history for the 60–90 days before the live scam week.
- data/validate.py
  - Validates all scenario files for schema correctness and project constraints.

### Scenario files
- data/scenarios/gold_bar.json
- data/scenarios/grandparent.json
- data/scenarios/phantom_hacker.json
- data/scenarios/home_buyer.json
- data/scenarios/coin_collector.json
- data/scenarios/car_buyer.json
- data/scenarios/crypto_investor.json
- data/scenarios/tax_payment.json

These files follow the structure in docs/CONTRACT.md and the story flow in docs/SCENARIOS.md.

## How to generate the normal history
From the repo root:

```bash
python .\data\make_history.py C1 --output .\data\scenarios\gold_bar_history.json
```

This produces a JSON history array for the given customer.

## How to validate all scenarios
From the repo root:

```bash
python .\data\validate.py
```

Expected result:

```text
Validated 8 scenario files in ...\data\scenarios
```

## Integration with engine work
The engine team will read the scenario JSON files and replay each `live` event in time order. The engine uses:
- customer metadata
- historical normal activity
- the sequential event chain
- trigger logic from docs/DECISION_SPEC.md

The engine expects output decisions in the exact shape defined in docs/CONTRACT.md.

## Integration with demo work
The demo page at demo/index.html consumes data in the same decision shape as the sample file in demo/sample_decisions.json.

When the engine is ready, the demo page can switch from the sample file to the real API output or replay file.

## Working rules
- Keep all new changes in the data folder unless the team explicitly approves another folder.
- Follow docs/CONTRACT.md exactly; do not invent new field names or values.
- Do not read the `truth` field in production engine logic.
- Keep the event timestamps in ISO format without timezone.
- Preserve lowercase action names in output decisions: allow, warn, pause, hold, escalate.

## Recommended handoff
Once the engine replay is running successfully, hand over:
1. scenario files used for tests
2. validation results
3. sample/demo replay data
4. final notes for the pitch video and evidence screenshots

## Summary
This data package gives the project:
- realistic normal customer behavior
- clean scam and non-scam story examples
- a reliable validation layer
- a ready-to-use scenario set for engine replay and demo playback
