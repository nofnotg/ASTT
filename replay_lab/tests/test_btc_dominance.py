import pandas as pd
from features.btc_dominance import compute_btc_dominance_regime


def test_btc_dominance_fallback_and_risk_off():
    btc = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=70, freq="min"), "close": [100] * 60 + [98] * 10})
    result = compute_btc_dominance_regime(btc, None, krw_breadth=0.2)
    assert result["alt_regime"] == "RISK_OFF"
    assert not result["alt_long_allowed"]


def test_btc_dominance_alt_risk_on():
    btc = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=70, freq="min"), "close": range(100, 170)})
    dom = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=70, freq="min"), "dominance": list(range(170, 100, -1))})
    assert compute_btc_dominance_regime(btc, dom, krw_breadth=0.7)["alt_regime"] == "ALT_RISK_ON"
