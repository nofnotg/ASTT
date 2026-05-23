from __future__ import annotations


SCENARIOS = {
    "gross": {"fee_pct": 0.0, "slippage_pct": 0.0, "latency_ms": 0},
    "fee_only": {"fee_pct": 0.05, "slippage_pct": 0.0, "latency_ms": 0},
    "realistic_1": {"fee_pct": 0.05, "slippage_pct": 0.05, "latency_ms": 500},
    "realistic_2": {"fee_pct": 0.05, "slippage_pct": 0.10, "latency_ms": 1000},
    "stress": {"fee_pct": 0.05, "slippage_pct": 0.15, "latency_ms": 2000},
}


def apply_micro_cost_model(trade_result: dict, scenario: str, orderbook_context=None) -> dict:
    cfg = SCENARIOS[scenario]
    gross = float(trade_result.get("realized_pnl_pct", trade_result.get("gross_pnl_pct", 0.0)))
    latency_cost = cfg["latency_ms"] / 1000 * 0.01
    cost = cfg["fee_pct"] * 2 + cfg["slippage_pct"] + latency_cost
    net = gross - cost
    return {"scenario": scenario, "gross_pnl_pct": gross, "net_pnl_pct": net, "cost_pct": cost, "latency_ms": cfg["latency_ms"], "slippage_pct": cfg["slippage_pct"], "survives_cost": net > 0}
