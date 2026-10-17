"""Every tunable number in the engine. Change values here, nowhere else.

Matches the "Settings" table in docs/DECISION_SPEC.md.
"""

# How long earlier triggers stay linked to new ones.
CHAIN_WINDOW_DAYS = 7

# T1 "unusual move": bigger than T1_MULTIPLIER x the customer's normal AND bigger than T1_FLOOR.
T1_MULTIPLIER = 5
T1_FLOOR = 5000

# T2: a first-time payee of an unknown type needs at least this much to fire.
T2_NEW_PAYEE_MIN = 10000

# Minimum outflow size that counts for T3 (repeat) and T5 (workaround).
LARGE_OUTFLOW = 5000

# T3 look-back for a previous large outflow.
REPEAT_DAYS = 7

# T5 look-back for an earlier pause / hold / escalate.
WORKAROUND_DAYS = 7

# Paid this payee at least this many times in history = trusted (skips all triggers).
TRUSTED_PAYEE_MIN_PAYMENTS = 2

# "Normal" amounts used when a customer's history has none of that type.
DEFAULT_NORMAL_TRANSFER = 1000
DEFAULT_NORMAL_CASH = 300

# Payee categories that always count as a risky destination for T2.
RISKY_CATEGORIES = {"gold_dealer", "crypto_exchange", "crypto_atm"}

# Display-only score. Does NOT decide the action.
SCORE_WEIGHTS = {"T1": 20, "T2": 30, "T3": 20, "RA": 15}
SCORE_T5_BONUS = 25

# Event types that move money out of the customer's accounts.
OUTFLOW_TYPES = {"cash_withdrawal", "wire", "payment"}
# Event types that move money at all (used for the remote-access trigger).
MONEY_TYPES = OUTFLOW_TYPES | {"internal_transfer"}

# Actions that mean "the bank stepped in" (this is T4 / intervention_active).
INTERVENTION_ACTIONS = {"pause", "hold", "escalate"}
HOLD_ACTIONS = {"hold", "escalate"}
