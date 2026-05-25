from __future__ import annotations

from market_data.market_history_filter import has_sufficient_history
from market_data.listed_age_classifier import classify_listed_age


def test_history_helpers_classify_coverage():
    assert has_sufficient_history(30, 36) is True
    assert has_sufficient_history(10, 36) is False
    assert classify_listed_age(2) == "NEWLY_LISTED"
    assert classify_listed_age(18) == "ESTABLISHED"
