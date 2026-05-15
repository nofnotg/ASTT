import pytest

from app.config import TradingMode, get_settings


def test_paper_mode_allows_missing_keys(monkeypatch):
    monkeypatch.delenv("UPBIT_ACCESS_KEY", raising=False)
    monkeypatch.delenv("UPBIT_SECRET_KEY", raising=False)
    settings = get_settings(TRADING_MODE="PAPER", LIVE_TRADING_ENABLED=False)
    assert settings.trading_mode == TradingMode.PAPER
    assert not settings.has_upbit_keys


def test_order_test_requires_keys(monkeypatch):
    monkeypatch.delenv("UPBIT_ACCESS_KEY", raising=False)
    monkeypatch.delenv("UPBIT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ORDER_TEST mode requires"):
        get_settings(TRADING_MODE="ORDER_TEST")


def test_live_requires_double_lock(monkeypatch):
    monkeypatch.setenv("UPBIT_ACCESS_KEY", "x")
    monkeypatch.setenv("UPBIT_SECRET_KEY", "y")
    with pytest.raises(RuntimeError, match="LIVE mode requires"):
        get_settings(TRADING_MODE="LIVE", LIVE_TRADING_ENABLED=False)
    settings = get_settings(TRADING_MODE="LIVE", LIVE_TRADING_ENABLED=True)
    assert settings.trading_mode == TradingMode.LIVE

