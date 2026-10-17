"""Turns whatever the scenario files contain into the types the engine expects.

Hand-written JSON is inconsistent: timestamps sometimes end in "Z", amounts are
sometimes strings like "80,000". Normalising here means one bad character in a data
file can't crash the engine in the middle of the demo.
"""

from datetime import datetime


def parse_timestamp(value):
    """ISO 8601 string (or datetime) -> naive datetime.

    A timezone, if present, is converted to UTC and then dropped, so naive and
    offset-aware timestamps in the same scenario can still be compared.
    """
    if isinstance(value, datetime):
        stamp = value
    else:
        text = str(value).strip().replace("Z", "+00:00").replace("z", "+00:00")
        stamp = datetime.fromisoformat(text)
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(tz=None).replace(tzinfo=None)
    return stamp


def to_amount(value):
    """Money -> float. Accepts 80000, 80000.0, "80000", "$80,000". None/blank -> 0.0."""
    if isinstance(value, bool) or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("$", "").replace(",", "").replace("_", "")
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def clean_event(event):
    """A copy of the event with `truth` removed and amount/timestamp normalised.

    The engine must never see `truth` (it is ground truth for scoring, not an input).
    """
    cleaned = {k: v for k, v in event.items() if k != "truth"}
    cleaned["amount"] = to_amount(cleaned.get("amount"))
    cleaned["_ts"] = parse_timestamp(cleaned["timestamp"])
    return cleaned
