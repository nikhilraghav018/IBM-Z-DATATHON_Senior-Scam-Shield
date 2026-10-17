# Scenarios (the stories the demo tells)

All live events happen in the week of **Mon Oct 19 to Sat Oct 24, 2026**.
All scam victims are `opted_in: true` with a trusted contact (otherwise the engine can never reach `hold`).

## Scam 1: Frisco gold bar scam (customer C1)

A caller posing as a federal agent says the victim's money is tied to a crime and must be "protected" as gold. A courier collects it.

| Day | What she does | Expected action |
|---|---|---|
| Mon | Moves $150,000 from investment to checking (online) | warn (T1) |
| Tue | Wires $80,000 to a gold dealer she has never paid | pause (T1 + T2) |
| Thu | Wires $60,000 to the same gold dealer again | hold (T5 after the pause) |
| Fri | Goes to a different branch to withdraw $40,000 cash | escalate (T5 while hold active) |

## Scam 2: Grandparent scam (customer C2)

A caller says her grandson is in jail and needs bail cash. A courier picks it up. She is told to say it's for home repairs.

| Day | What she does | Expected action |
|---|---|---|
| Mon | $9,000 cash at Branch A (she normally takes out ~$200) | warn (T1) |
| Wed | $15,000 cash at Branch B, "home repairs" | pause (T1 + T3) |
| Sat | $25,000 cash at Branch C | hold (T5 after the pause) |

## Scam 3: Phantom hacker scam (customer C3)

Fake tech support gets remote access, a fake bank employee says the account is hacked, a fake "government official" says move everything to a safe account.

| Day | What he does | Expected action |
|---|---|---|
| Mon | Logs in with remote-access software running | allow (RA starts) |
| Mon | Moves $200,000 from savings to checking in the same session | pause (RA + T1) |
| Tue | Wires $200,000 to a new payee "Federal Reserve Safe Account" | hold (T5 after the pause) |
| Wed | Withdraws $40,000 cash at a branch (told to feed a crypto ATM) | escalate (T5 while hold active) |

## Innocent look-alikes (must never be paused or held)

| Customer | Story | Why it stays clean |
|---|---|---|
| C4 Home buyer | Mon: $120,000 savings to checking. Wed: $118,500 wire to Collin County Title (`title_escrow`, `payee_verified: true`) | Verified payee, so Wednesday fires nothing. Only a Monday warning |
| C5 Coin collector | Tue: $3,000 payment to Heritage Coins (`gold_dealer`), same dealer every month in history | Trusted payee (paid 2+ times) |
| C6 Car buyer | Wed: one $20,000 cash withdrawal at home branch, nothing after | One trigger only, so warn |
| C7 Crypto investor | Thu: $500 to Coinbase, same as every month in history | Trusted payee, small amount |
| C8 Tax payment | Mon: $30,000 savings to checking. Thu: $28,000 payment to IRS (`government`, `payee_verified: true`) | Verified payee |

## Normal history (for every customer, 60 to 90 days before Oct 19)

Enough everyday life that the engine can learn "normal":
- Monthly `deposit` (Social Security or pension)
- Weekly grocery and pharmacy `payment`s ($40 to $200)
- Monthly utility `payment` (verified)
- A few ATM `cash_withdrawal`s ($100 to $300) at the home branch
- A couple of small `internal_transfer`s savings to checking ($500 to $1,500)
- C5 only: monthly $2,000 to $4,000 payment to Heritage Coins
- C7 only: monthly $300 to $700 payment to Coinbase

## Pitch numbers to compare against

A "single-transaction rule" (what banks do today, simplified): flag any single outflow >= $50,000, or any wire >= $25,000 to a first-time payee.
- It misses the grandparent scam completely (every withdrawal is under $50,000)
- It falsely flags the home buyer's $118,500 title wire
- It never sees the branch workaround as connected to anything
