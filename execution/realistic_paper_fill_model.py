from __future__ import annotations


SCENARIOS = {
    "gross": {"fee_pct": 0.0, "slippage_pct": 0.0, "latency_ms": 0},
    "fee_only": {"fee_pct": 0.05, "slippage_pct": 0.0, "latency_ms": 0},
    "realistic_1": {"fee_pct": 0.05, "slippage_pct": 0.05, "latency_ms": 500},
    "realistic_2": {"fee_pct": 0.05, "slippage_pct": 0.10, "latency_ms": 1000},
    "stress": {"fee_pct": 0.05, "slippage_pct": 0.15, "latency_ms": 2000},
}


def simulate_entry_fill(candidate: dict, snapshot: dict, order_krw: float, scenario: str = "realistic_1") -> dict:
    cfg = SCENARIOS[scenario]
    ask = float(snapshot.get("best_ask") or snapshot.get("last_price", 0.0))
    if ask <= 0:
        return {"fill_price": 0.0, "fee_krw": 0.0, "slippage_pct": cfg["slippage_pct"], "latency_ms": cfg["latency_ms"], "fill_possible": False, "reject_reason": "NO_ASK_PRICE"}
    fill_price = ask * (1 + cfg["slippage_pct"] / 100)
    return {"fill_price": fill_price, "fee_krw": order_krw * cfg["fee_pct"] / 100, "slippage_pct": cfg["slippage_pct"], "latency_ms": cfg["latency_ms"], "fill_possible": True, "reject_reason": None}


def simulate_exit_fill(position: dict, snapshot: dict, reason: str, scenario: str = "realistic_1") -> dict:
    cfg = SCENARIOS[scenario]
    bid = float(snapshot.get("best_bid") or snapshot.get("last_price", 0.0))
    if bid <= 0:
        return {"fill_price": 0.0, "fee_krw": 0.0, "slippage_pct": cfg["slippage_pct"], "latency_ms": cfg["latency_ms"], "fill_possible": False, "reject_reason": "NO_BID_PRICE", "reason": reason}
    fill_price = bid * (1 - cfg["slippage_pct"] / 100)
    order_krw = float(position.get("order_krw", 0.0))
    return {"fill_price": fill_price, "fee_krw": order_krw * cfg["fee_pct"] / 100, "slippage_pct": cfg["slippage_pct"], "latency_ms": cfg["latency_ms"], "fill_possible": True, "reject_reason": None, "reason": reason}
