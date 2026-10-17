# ml/ : ML risk score on Telum

**Owner:** Nikhil
**Goal:** add a model's scam-risk score next to every decision. **The rules keep deciding the action;
the model only adds a number.** A bonus for the Technical Design score (2 AI frameworks + Telum), not a
dependency: the demo works without it.

| File | What it does |
|---|---|
| `scam_risk_model.ipynb` | The whole story: generate data, train both models, held-out test, export, Telum timing, check nothing broke. Run it in Jupyter on LinuxONE |
| `population.py` | Synthetic population: thousands of customers built on `data/make_history.py`, ~2% with randomised scam chains, ~12% innocent look-alikes. Stdlib only |
| `features.py` | `MLEngine`: the rules engine with 5 extra features (payee trust, event type). Same rules, same actions |
| `scorer.py` | Runs the exported network in plain Python, for `MLEngine(scorer=load_scorer())`. No installs |
| `model.json` | The exported network (11 KB). The notebook regenerates it |

## The honest test
We wrote both the scam patterns and the rules, so testing on a known scam type would score ~99% and prove
nothing. Instead: **train on two scam types, test on the third**, with the model allowed **no more false
alarms than the rules**. A scam counts as caught only if a money-leaving event (payment, wire, cash) gets
flagged.

Caveat to say out loud: the gradient boosting model leans mostly on `triggers_fired`, which the rules
compute. The notebook also reports a version without the rule features so you can see what the model
finds on its own.

## Run it on LinuxONE
Open `ml/scam_risk_model.ipynb` in the Jupyter container (port 38888) from inside the repo and
**Run All**. About a minute. It needs numpy, scikit-learn and tensorflow, which the
`jupyterlab-image-s390x` image ships with. Peak memory is well under 1 GB.

## Run it on a laptop
```bash
pip install numpy scikit-learn tensorflow jupyter
jupyter lab ml/scam_risk_model.ipynb
```

## Not wired into the live API (yet)
On purpose: Kamali is recording from the live API tonight and the container must not be restarted.
Wiring it in later is a 3-line change in `api/main.py` (use `MLEngine(scorer=load_scorer())` when
`ml/model.json` exists).
