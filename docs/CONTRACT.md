# Data Contract (the shared language of the project)

Every folder in this repo talks to the others using the JSON shapes below.
**Do not rename fields or change allowed values without telling the whole team.**
If the backend sends `"HOLD"` and the demo expects `"hold"`, things break.

All money is in US dollars as a plain number (no `$`, no commas): `80000`, not `"$80,000"`.
All times are ISO 8601 without timezone: `"2026-10-19T10:05:00"`.

---

## 1. Customer

```json
{
  "customer_id": "C1",
  "name": "Margaret Hill",
  "age": 78,
  "opted_in": true,
  "trusted_contact": { "name": "Susan Hill", "relation": "daughter", "phone": "+1-214-555-0142" },
  "home_branch": "BR-FRISCO-1"
}
```

| Field | Type | Notes |
|---|---|---|
| `customer_id` | string | Unique. `C1`, `C2`, ... |
| `name` | string | Fake name |
| `age` | integer | |
| `opted_in` | boolean | If `false`, the engine never goes above `pause` and never alerts family |
| `trusted_contact` | object or `null` | Only used when `opted_in` is `true` |
| `home_branch` | string | Branch the customer normally uses |

---

## 2. Event (what goes INTO the engine)

```json
{
  "event_id": "C1-E005",
  "customer_id": "C1",
  "timestamp": "2026-10-20T11:20:00",
  "type": "wire",
  "channel": "online",
  "amount": 80000,
  "from_account": "checking",
  "to_account": null,
  "payee_id": "P-LSB",
  "payee_name": "Lone Star Bullion",
  "payee_category": "gold_dealer",
  "payee_verified": false,
  "branch_id": null,
  "remote_access": false,
  "truth": "scam"
}
```

| Field | Type | Allowed values / notes |
|---|---|---|
| `event_id` | string | Unique. Suggested: `<customer>-E<number>` |
| `customer_id` | string | Must match a customer |
| `timestamp` | string | ISO 8601, e.g. `2026-10-20T11:20:00` |
| `type` | string | `login`, `internal_transfer`, `cash_withdrawal`, `wire`, `payment`, `deposit` |
| `channel` | string | `online`, `branch`, `phone`, `atm` |
| `amount` | number | `0` for `login` |
| `from_account` | string or `null` | `checking`, `savings`, `investment` |
| `to_account` | string or `null` | Only for `internal_transfer`: `checking`, `savings`, `investment` |
| `payee_id` | string or `null` | Only for `wire` and `payment`. Same payee = same id every time |
| `payee_name` | string or `null` | Human readable, shown in the demo |
| `payee_category` | string or `null` | `grocery`, `pharmacy`, `utility`, `retail`, `gold_dealer`, `crypto_exchange`, `crypto_atm`, `title_escrow`, `government`, `auto_dealer`, `contractor`, `medical`, `person`, `unknown` |
| `payee_verified` | boolean | `true` only for bank-verified billers (IRS, title companies, utilities) |
| `branch_id` | string or `null` | Required when `channel` is `branch` or `atm` |
| `remote_access` | boolean | `true` if remote-control software was detected in the session |
| `truth` | string | `scam` or `normal`. **Ground truth for scoring only. The engine must never read this field.** |

Money direction cheat sheet:
- **Outflows** (money leaving the customer): `cash_withdrawal`, `wire`, `payment`
- **Not outflows**: `internal_transfer` (between their own accounts), `deposit`, `login`

---

## 3. Decision (what comes OUT of the engine)

```json
{
  "event_id": "C1-E005",
  "customer_id": "C1",
  "timestamp": "2026-10-20T11:20:00",
  "action": "pause",
  "triggers_fired": ["T2"],
  "chain": ["T1", "T2"],
  "intervention_active": false,
  "risk_score": 50,
  "reasons": [
    "Oct 19: $150,000 moved from investment to checking (about 150x this customer's usual transfer)",
    "Oct 20: first payment to a gold dealer (Lone Star Bullion, $80,000)"
  ],
  "messages": {
    "customer": "We've paused this payment to protect you. A member of our team will call you at the phone number we have on file.",
    "staff": "PAUSE: call the customer on the number on file, not one they give you. Ask: Has anyone asked you to keep this payment secret, or told you what to say to the bank?",
    "family": null
  },
  "money_released": false
}
```

| Field | Type | Notes |
|---|---|---|
| `event_id`, `customer_id`, `timestamp` | | Copied from the event |
| `action` | string | `allow`, `warn`, `pause`, `hold`, `escalate` (lowercase, exactly these) |
| `triggers_fired` | list of strings | Triggers caused by THIS event. Values: `T1`, `T2`, `T3`, `T5`, `RA` |
| `chain` | list of strings | Distinct triggers from the last 7 days including this event. Values: `T1`, `T2`, `T3`, `RA` (T5 is never in the chain, it is handled separately) |
| `intervention_active` | boolean | This is "T4": `true` if the bank paused/held/escalated something for this customer in the last 7 days, before this event |
| `risk_score` | integer 0 to 100 | For display only. Does not decide the action |
| `reasons` | list of strings | Plain English, one line per trigger in the chain |
| `messages.customer` | string or `null` | Shown to the customer. `null` for `allow` |
| `messages.staff` | string or `null` | Shown to the bank employee. `null` for `allow` and `warn` |
| `messages.family` | string or `null` | Only for `hold`/`escalate` AND `opted_in` is `true`. Never contains amounts or account details |
| `money_released` | boolean | `true` for `allow` and `warn`, `false` for `pause`, `hold`, `escalate` |

### Badge colors for the demo

| action | color |
|---|---|
| `allow` | green |
| `warn` | yellow |
| `pause` | orange |
| `hold` | red |
| `escalate` | dark red / purple |

---

## 4. Scenario file (what the data folder produces)

One file per story in `data/scenarios/`, e.g. `data/scenarios/gold_bar.json`:

```json
{
  "scenario": "gold_bar",
  "description": "Frisco-style gold bar scam over 5 days",
  "customer": { "...": "Customer object" },
  "history": [ "...60 to 90 days of normal Event objects, truth = normal" ],
  "live": [ "...the story events in time order, truth = scam or normal" ]
}
```

- `history` is what the engine learns "normal" from (usual cash amount, usual transfers, known payees).
- `live` is what gets replayed in the demo, one decision per event.

---

## 5. Replay item (what the demo page receives)

The demo needs to show both what happened and what the bank decided, so `/demo/replay`
(and `demo/decisions.json`) return a **list of pairs**, sorted by `event.timestamp`:

```json
[
  {
    "customer": { "customer_id": "C1", "name": "Margaret Hill", "age": 78, "opted_in": true },
    "event":    { "...": "Event object" },
    "decision": { "...": "Decision object" }
  }
]
```

`customer` here only needs `customer_id`, `name`, `age`, `opted_in`. See `demo/sample_decisions.json` for a full example.
