import pandas as pd

from replay_lab.replay.structure_reversal_v5 import StructureReversalV5Config, evaluate_structure_reversal_candidate, live_readiness_v5


def _frame(rows=120):
    return pd.DataFrame({"time": pd.date_range("2026-01-01", periods=rows, freq="min"), "open": range(100, 100 + rows), "high": range(101, 101 + rows), "low": range(99, 99 + rows), "close": range(100, 100 + rows), "volume": [100] * rows, "trade_price": [10000] * rows})


def test_v5_candidate_and_readiness(monkeypatch):
    frame = _frame()
    context = {"weekly": frame, "daily": frame, "h4": frame, "h1": frame, "m15": frame, "m5": frame, "m1": frame, "btc_m5": frame}
    result = evaluate_structure_reversal_candidate(context, "KRW-BTC", pd.Timestamp("2026-01-01"), StructureReversalV5Config(weekly_min_score=0, daily_min_score=0, h4_min_score=0, v5_min_score=0))
    assert "risk_gate" in result
    assert result["v5"]["v5_score"] >= 0
    assert live_readiness_v5({"entry_count": 30, "account_return_pct": 1, "profit_factor": 1.2, "max_drawdown_pct": -1, "consecutive_loss_max": 3, "risk_gate_active": True}) == "MICRO_LIVE_READY"
