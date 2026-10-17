# Decision Spec (how the engine decides)

Owner: engine team. Decided Oct 17, 2026.
Design rule for this datathon: **keep it simple and explainable.** Every number below is a named setting so it can be tuned in one place.

## Settings (defaults)

| Setting | Value | Used by |
|---|---|---|
| `CHAIN_WINDOW_DAYS` | 7 | How long earlier triggers stay linked |
| `T1_MULTIPLIER` | 5 | "Unusual" = more than 5x the customer's normal |
| `T1_FLOOR` | 5000 | ...and more than $5,000 |
| `T2_NEW_PAYEE_MIN` | 10000 | First-time payee of an unknown type needs $10,000+ to fire T2 |
| `LARGE_OUTFLOW` | 5000 | Minimum size for T3 and T5 |
| `REPEAT_DAYS` | 7 | T3 look-back |
| `WORKAROUND_DAYS` | 7 | T5 look-back after the bank stepped in |
| `TRUSTED_PAYEE_MIN_PAYMENTS` | 2 | Paid this payee 2+ times in history = trusted |

"The customer's normal" is computed from their `history`:
- normal transfer = the largest `internal_transfer` into checking in their history (use 1000 if none)
- normal cash = the largest `cash_withdrawal` in their history (use 300 if none)

## Step 0: Trusted destination skip rule

If the event is a `wire` or `payment` AND (`payee_verified` is `true` OR the customer paid this `payee_id` at least 2 times in history), then **no triggers fire** for this event. Action = `allow`.

This is what protects the coin collector (same dealer every month) and the home buyer (verified title company).

## Step 1: Triggers

| Trigger | Fires when |
|---|---|
| **T1** Unusual move | `internal_transfer` from `savings` or `investment` to `checking` with amount > max(5 x normal transfer, $5,000), **or** `cash_withdrawal` with amount > max(5 x normal cash, $5,000) |
| **T2** Risky destination | Outflow (`wire`/`payment`) to an untrusted payee where `payee_category` is `gold_dealer`, `crypto_exchange` or `crypto_atm`, **or** the payee is new to this customer and amount >= $10,000 |
| **T3** Repeat | Outflow >= $5,000 (not to a trusted payee) AND there was another outflow >= $5,000 in the last 7 days. Attempts count even if the bank paused them |
| **T4** Bank stepped in | Not a trigger. It is the state `intervention_active`: the engine paused, held or escalated something for this customer in the last 7 days |
| **T5** Workaround | Outflow >= $5,000 (not to a trusted payee) while `intervention_active` is `true` |
| **RA** Remote access | A `login` with `remote_access: true` happened earlier the same day, or the event itself has `remote_access: true`, and this event moves money |

`login` events never fire T1/T2/T3/T5. A `login` with `remote_access: true` returns `allow` but starts the RA flag for the rest of that day.

## Step 2: Pick the action

`chain` = distinct triggers among {T1, T2, T3, RA} from this customer's events in the last 7 days, including this one.

Check these in order, first match wins:

| # | Condition | Action |
|---|---|---|
| 1 | This event fired no triggers | `allow` |
| 2 | T5 fired AND a `hold` or `escalate` is already active | `escalate` |
| 3 | T5 fired | `hold` |
| 4 | chain has 3 or more triggers | `hold` |
| 5 | chain has 2 triggers | `pause` |
| 6 | chain has 1 trigger | `warn` |

Rule 1 matters: a clean event is allowed even if the customer had warnings earlier this week.

## Step 3: Opt-in cap

If `opted_in` is `false`: `hold` and `escalate` become `pause`, and `messages.family` is always `null`.

## Display score (does NOT decide anything)

`risk_score` = sum of weights for triggers in `chain` (T1 = 20, T2 = 30, T3 = 20, RA = 15), plus 25 if T5 fired on this event, capped at 100.

## Message templates

| Action | Customer | Staff | Family (opted in only) |
|---|---|---|---|
| allow | `null` | `null` | `null` |
| warn | "Reminder: your bank, the police and government agencies will never ask you to move money to keep it safe, buy gold, or hand cash to a courier." | `null` | `null` |
| pause | "We've paused this payment to protect you. A member of our team will call you at the phone number we have on file." | "PAUSE: call the customer on the number on file, not one they give you. Ask: Has anyone asked you to keep this payment secret, or told you what to say to the bank?" | `null` |
| hold | "This payment is on a short hold while we make sure you are safe. We will call you today." | "HOLD: senior scam pattern. Call the customer, then the trusted contact. Do not release funds until verified." | "Hi {contact_name}, {first_name} asked us to let you know if something looked unusual. Please check in with them today." |
| escalate | "This payment is still on hold. A branch manager will contact you personally." | "ESCALATE: repeated attempts after a hold. Manager review required. Consider an Adult Protective Services referral." | same as hold |

Family messages never include amounts, payees or account details.

## Reasons (plain English, one per trigger in the chain)

For `allow`, `reasons` is a single line saying why it was allowed: "Verified payee ({payee_name})", "Trusted payee, paid {n} times before", or "Normal activity for this customer".
For every other action, one line per trigger in the chain:

- T1: "{date}: ${amount} moved from {from} to checking (about {N}x this customer's usual transfer)" or "{date}: ${amount} cash withdrawal (about {N}x their usual)"
- T2: "{date}: first payment to a {category} ({payee_name}, ${amount})"
- T3: "{date}: another large outflow within {d} days (${total} in the last 7 days)"
- T5: "{date}: new attempt to move money after the bank already stepped in"
- RA: "{date}: remote-access software was active during this session"

## Expected results for the demo (use these as tests)

| Scenario | Must happen |
|---|---|
| Gold bar | Ends in `hold` then `escalate` before the final cash leaves |
| Grandparent | Reaches `hold` by the third branch withdrawal |
| Phantom hacker | `pause` on the big savings move, `hold` on the "safe account" wire |
| Home buyer, coin collector, car buyer, tax payment, crypto investor | **Never** `pause`, `hold` or `escalate` |
