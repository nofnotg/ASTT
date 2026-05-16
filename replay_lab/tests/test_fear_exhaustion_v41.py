import pandas as pd

from replay_lab.replay.fear_exhaustion_v41 import FearExhaustionV41Config, evaluate_v41_candidate, live_readiness_v41


def test_v41_candidate_allows_relaxed_exhaustion(monkeypatch):
    frame = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=80, freq="min"),
            "open": [100] * 80,
            "high": [101] * 80,
            "low": [99] * 80,
            "close": [100] * 80,
            "volume": [100] * 80,
            "trade_price": [10000] * 80,
            "fear_score": [50] * 80,
        }
    )
    monkeypatch.setattr("replay_lab.replay.fear_exhaustion_v41.detect_drop_event", lambda *a, **k: {"has_drop_event": True, "drop_speed_score": 80, "drop_pct": 1.2})
    monkeypatch.setattr("replay_lab.replay.fear_exhaustion_v41.detect_low_retest_or_lower_low", lambda *a, **k: {"pattern": "LOW_RETEST", "low_structure_score": 70, "low_2": 99})
    monkeypatch.setattr("replay_lab.replay.fear_exhaustion_v41.detect_fear_cooling", lambda *a, **k: {"has_fear_cooling": True, "cooling_score": 75, "cooling_type": "MIXED"})
    monkeypatch.setattr("replay_lab.replay.fear_exhaustion_v41.detect_lower_band_reentry", lambda *a, **k: {"reentered_lower_band": True, "reentry_strength": 80, "middle_band": 101, "lower_band": 98})
    monkeypatch.setattr("replay_lab.replay.fear_exhaustion_v41.evaluate_min_support_context", lambda *a, **k: {"has_min_support": True, "support_context_score": 70, "support_sources": ["PREVIOUS_LOW"], "target_space_pct": 0.8})
    monkeypatch.setattr("replay_lab.replay.fear_exhaustion_v41._liquidity_context", lambda *a, **k: {"liquidity_score": 80})
    monkeypatch.setattr("replay_lab.replay.fear_exhaustion_v41._risk_context", lambda *a, **k: {"falling_knife_speed_pct": -0.5, "close_position": 0.8})
    result = evaluate_v41_candidate(frame, "KRW-BTC", FearExhaustionV41Config(min_v41_score=60))
    assert result["score_pass"]
    assert result["blocking_applied"] is False
    assert result["v41_score"] >= 60


def test_v41_live_readiness_thresholds():
    assert live_readiness_v41({"entry_count": 30, "account_return_pct": 1.0, "profit_factor": 1.2, "max_drawdown_pct": -2, "consecutive_loss_max": 3}) == "MICRO_LIVE_READY"
    assert live_readiness_v41({"entry_count": 10}) == "LIVE_NOT_ALLOWED"
