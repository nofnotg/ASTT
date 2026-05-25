from __future__ import annotations


def classify_listed_age(months_available: float) -> str:
    if months_available < 3:
        return "NEWLY_LISTED"
    if months_available < 12:
        return "SHORT_HISTORY"
    return "ESTABLISHED"
