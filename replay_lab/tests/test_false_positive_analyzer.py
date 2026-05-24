from winner_mining.false_positive_analyzer import _fires_source


def test_false_positive_source_rules():
    row = {"buy_trade_ratio_10s": 0.6, "orderbook_imbalance": 0.1, "spread_pct": 0.1}
    assert _fires_source("ORDERFLOW_SURGE", row) is True
    assert _fires_source("ORDERFLOW_SURGE", {**row, "spread_pct": 0.9}) is False
