from tradable_winner.tradable_winner_prefilter import apply_tradable_winner_prefilter


def _book(spread_wide=False, shallow=False):
    if spread_wide:
        return {"units": [{"ask_price": 102, "bid_price": 100, "ask_size": 10000, "bid_size": 10000}]}
    size = 1000 if shallow else 20000
    return {"units": [{"ask_price": 100.1, "bid_price": 100.0, "ask_size": size, "bid_size": size}, {"ask_price": 100.2, "bid_price": 99.9, "ask_size": size, "bid_size": size}, {"ask_price": 100.3, "bid_price": 99.8, "ask_size": size, "bid_size": size}, {"ask_price": 100.4, "bid_price": 99.7, "ask_size": size, "bid_size": size}, {"ask_price": 100.5, "bid_price": 99.6, "ask_size": size, "bid_size": size}]}


def test_prefilter_rejects_spread_depth_and_effective_return():
    spread = apply_tradable_winner_prefilter("KRW-AAA", 100, 101, _book(spread_wide=True), "TRADABLE_SCALP_WINNER", 10, 10)
    assert "SPREAD_TOO_WIDE" in spread["reject_reasons"]
    depth = apply_tradable_winner_prefilter("KRW-AAA", 100, 101, _book(shallow=True), "TRADABLE_SCALP_WINNER", 10, 10)
    assert "DEPTH_INSUFFICIENT" in depth["reject_reasons"]
    weak = apply_tradable_winner_prefilter("KRW-AAA", 100, 100.1, _book(), "TRADABLE_SCALP_WINNER", 10, 10)
    assert "EFFECTIVE_RETURN_TOO_LOW" in weak["reject_reasons"]
