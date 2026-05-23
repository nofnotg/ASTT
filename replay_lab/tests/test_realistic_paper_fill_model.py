from execution.realistic_paper_fill_model import simulate_entry_fill, simulate_exit_fill


def test_fill_model_uses_best_ask_for_entry_and_best_bid_for_exit():
    entry = simulate_entry_fill({}, {"best_ask": 100, "last_price": 100}, 10000)
    assert entry["fill_price"] > 100
    assert entry["fee_krw"] > 0
    exit_fill = simulate_exit_fill({"order_krw": 10000}, {"best_bid": 101, "last_price": 101}, "TAKE_PROFIT")
    assert exit_fill["fill_price"] < 101
    assert exit_fill["fee_krw"] > 0
