from features.micro_cost_model import apply_micro_cost_model


def test_micro_cost_model_scenarios_reduce_pnl():
    gross = apply_micro_cost_model({"realized_pnl_pct": 0.3}, "gross")
    realistic = apply_micro_cost_model({"realized_pnl_pct": 0.3}, "realistic_1")

    assert gross["net_pnl_pct"] == 0.3
    assert realistic["net_pnl_pct"] < gross["net_pnl_pct"]
    assert realistic["latency_ms"] == 500
