import pandas as pd

from ict_strategy.order_block_detector import detect_order_blocks


def test_order_block_detector_detects_bullish_block():
    rows = [{"open": 100, "close": 100, "high": 101, "low": 99, "volume": 1} for _ in range(9)]
    rows += [{"open": 100, "close": 99, "high": 101, "low": 98, "volume": 2}, {"open": 99, "close": 103, "high": 104, "low": 98, "volume": 4}]
    assert any(block["zone_type"] == "BULLISH_ORDER_BLOCK" for block in detect_order_blocks(pd.DataFrame(rows)))
