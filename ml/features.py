"""The feature vector the ML risk score sees. Standard library only.

`MLEngine` is the rules engine with a few extra numbers in `features()`. It does not
change any rule or any action: `process()` is inherited untouched, so every decision is
identical to `engine.engine.Engine`. (`api/test` and `engine.test_engine` still cover that.)

Why the extras: the engine's 13 features don't say whether a payee is bank-verified
(a title company, the IRS) or one the customer has paid many times. That is exactly what
lets the rules wave a home purchase or a tax bill through, so without it the model
mistakes those for scams.
"""

import math

from engine.engine import Engine
from engine.triggers import is_trusted_payee

# Heavy-tailed money amounts and ratios are fed to the model as log(1 + x).
LOG_FEATURES = {"amount", "amount_vs_normal_transfer", "amount_vs_normal_cash", "total_outflow_7d"}

# Features computed from the rules' own output. Reported separately in the notebook, so we
# can say how much of the score is "the model re-reading the rules".
RULE_FEATURES = {"chain_length", "triggers_fired"}


class MLEngine(Engine):
    """Engine whose features() adds payee trust and event type. Rules and actions unchanged."""

    @staticmethod
    def features(event, profile, chain, fired, recent):
        f = Engine.features(event, profile, chain, fired, recent)
        f["is_trusted_payee"] = float(is_trusted_payee(event, profile))
        f["is_verified_payee"] = float(bool(event.get("payee_verified")))
        f["is_wire"] = float(event.get("type") == "wire")
        f["is_cash"] = float(event.get("type") == "cash_withdrawal")
        f["is_transfer_in"] = float(event.get("type") == "internal_transfer")
        return f


def to_vector(features, names):
    """Feature dict -> list of floats in `names` order, with the log transform applied."""
    return [math.log1p(max(features[n], 0.0)) if n in LOG_FEATURES else float(features[n]) for n in names]
