from app.config import get_settings
from personas.iris import analyze


def test_risk_reward_veto():
    settings = get_settings(TRADING_MODE="PAPER")
    result = analyze({"market": "KRW-BTC", "risk_reward": 1.2, "krw_amount": 5000}, settings)
    assert result.veto
    assert result.veto_reason == "risk_reward_below_1.5"


def test_websocket_quality_veto():
    settings = get_settings(TRADING_MODE="PAPER")
    result = analyze({"market": "KRW-BTC", "risk_reward": 2.0, "data_quality_warning": "websocket gap", "krw_amount": 5000}, settings)
    assert result.veto
    assert result.veto_reason == "data_quality_warning"


def test_daily_loss_veto():
    settings = get_settings(TRADING_MODE="PAPER", MAX_DAILY_LOSS_PCT=1.5)
    result = analyze({"market": "KRW-BTC", "risk_reward": 2.0, "daily_loss_pct": -2.0, "krw_amount": 5000}, settings)
    assert result.veto
    assert result.veto_reason == "max_daily_loss_reached"

