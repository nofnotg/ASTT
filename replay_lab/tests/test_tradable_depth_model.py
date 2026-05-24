from tradable_winner.tradable_depth_model import calculate_orderbook_depth_krw, is_tradable_depth


def test_depth_model_uses_min_side_depth():
    orderbook = {"units": [{"ask_price": 100, "ask_size": 7000, "bid_price": 99, "bid_size": 8000}, {"ask_price": 101, "ask_size": 5000, "bid_price": 98, "bid_size": 5000}]}
    depth = calculate_orderbook_depth_krw(orderbook, levels=2)
    assert depth["depth_krw"] >= 1_000_000
    assert is_tradable_depth(orderbook, 1_000_000, levels=2)["tradable"] is True
