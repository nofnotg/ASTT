import pandas as pd

from replay_lab.replay.fear_divergence_v4 import FearDivergenceConfig, evaluate_v4_candidate, live_readiness_v4


def test_v4_candidate_requires_skeptic_pass(monkeypatch):
    frame = pd.DataFrame({"time": range(80), "open": [100] * 80, "high": [101] * 80, "low": [99] * 80, "close": [100] * 80, "volume": [100] * 80, "trade_price": [10000] * 80, "fear_score": [20] * 80})
    monkeypatch.setattr("replay_lab.replay.fear_divergence_v4.detect_bullish_fear_divergence", lambda *a, **k: {"has_bullish_fear_divergence": True, "divergence_strength": 80, "price_low_2": 99})
    monkeypatch.setattr("replay_lab.replay.fear_divergence_v4.detect_lower_band_reentry", lambda *a, **k: {"reentered_lower_band": True, "reentry_strength": 80, "middle_band": 101})
    monkeypatch.setattr("replay_lab.replay.fear_divergence_v4.body_zone_context", lambda *a, **k: {"body_zone_score": 60, "target_space_pct": 1.2})
    monkeypatch.setattr("replay_lab.replay.fear_divergence_v4.detect_trendline_bounce", lambda *a, **k: {"trendline_score": 60})
    result = evaluate_v4_candidate(frame, "KRW-BTC", FearDivergenceConfig(min_v4_score=70))
    assert result["is_candidate"]
    assert result["skeptic"]["skeptic_decision"] == "PASS"


def test_v4_live_readiness_requires_all_thresholds():
    assert live_readiness_v4({"entry_count": 30, "win_rate": 0.5, "profit_factor": 1.2, "account_return_pct": 0.1, "max_drawdown_pct": -1, "consecutive_loss_max": 3}, True) == "MICRO_LIVE_READY"
    assert live_readiness_v4({"entry_count": 2}, True) == "LIVE_NOT_ALLOWED"
