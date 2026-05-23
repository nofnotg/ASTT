from features.ema_pullback_candidate import detect_ema_pullback_candidate


def test_ema_pullback_candidate():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 100, "price_change_5s_pct": 0.1, "buy_trade_ratio_5s": 0.6}
    assert detect_ema_pullback_candidate("KRW-BTC", snap, {"ema20": 100, "ema50": 99})["candidate_source"] == "EMA_PULLBACK"


def test_ema_pullback_none_when_trend_missing():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 100, "price_change_5s_pct": 0.1, "buy_trade_ratio_5s": 0.6}
    assert detect_ema_pullback_candidate("KRW-BTC", snap, {"ema20": 99, "ema50": 100}) is None
