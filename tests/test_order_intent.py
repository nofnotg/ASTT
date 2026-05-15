import pytest

from execution.order_intent import create_entry_intent, validate_min_order


def test_order_intent_creation():
    intent = create_entry_intent(1, "KRW-BTC", 5000, "PAPER")
    assert intent.identifier.startswith("astt-KRW-BTC-bid-")
    assert intent.ord_type == "price"


def test_identifier_is_unique_enough():
    a = create_entry_intent(1, "KRW-BTC", 5000, "PAPER")
    b = create_entry_intent(1, "KRW-BTC", 5000, "PAPER")
    assert a.identifier != b.identifier


def test_min_order_guard():
    intent = create_entry_intent(1, "KRW-BTC", 4999, "PAPER")
    with pytest.raises(ValueError, match="below"):
        validate_min_order(intent, 5000)

