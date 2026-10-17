"""Run the trained Keras network without Keras. Standard library only.

The notebook exports the small network's weights to `ml/model.json`. This file does the
same maths (a few dense layers) in plain Python, so the engine and the API container can
use the model with zero installs on LinuxONE.

    from ml.features import MLEngine
    from ml.scorer import load_scorer

    eng = MLEngine(scorer=load_scorer())    # every decision gets decision["ml"]

The rules still decide the action. The model only adds a number.
"""

import json
import math
import time
from pathlib import Path

from ml.features import to_vector

MODEL_PATH = Path(__file__).resolve().parent / "model.json"

ACTIVATIONS = {
    "relu": lambda x: x if x > 0.0 else 0.0,
    "sigmoid": lambda x: 1.0 / (1.0 + math.exp(-x)) if x >= -60 else 0.0,
    "linear": lambda x: x,
}


def load_model(path=MODEL_PATH):
    with Path(path).open() as f:
        return json.load(f)


def predict(model, features):
    """Feature dict -> scam probability between 0 and 1."""
    x = to_vector(features, model["features"])
    x = [(v - m) / s for v, m, s in zip(x, model["mean"], model["std"])]
    for layer in model["layers"]:
        act = ACTIVATIONS[layer["activation"]]
        # W is stored as [inputs][outputs], like Keras.
        x = [
            act(b + sum(xi * row[j] for xi, row in zip(x, layer["W"])))
            for j, b in enumerate(layer["b"])
        ]
    return x[0]


def load_scorer(path=MODEL_PATH):
    """Return scorer(features) -> {"risk", "flag", "model", "ms"} for Engine(scorer=...)."""
    model = load_model(path)

    def scorer(features):
        start = time.perf_counter()
        risk = predict(model, features)
        return {
            "risk": round(risk, 3),
            # Only money leaving the bank can be flagged; see the notebook for why.
            "flag": bool(risk >= model["threshold"] and features.get("is_outflow")),
            "model": model["name"],
            "ms": round((time.perf_counter() - start) * 1000, 3),
        }

    return scorer
