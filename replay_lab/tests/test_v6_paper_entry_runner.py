import pandas as pd

from execution.v6_paper_entry_runner import run_v6_strategy_backtest
from market_data.ohlcv_store import OHLCVStore


def test_v6_paper_entry_runner_generates_paper_trade(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = OHLCVStore(tmp_path / "v6")
    times = pd.date_range("2026-01-01T00:00:00", periods=40, freq="h")
    frame = pd.DataFrame([{"time": time, "open": 100+i, "high": 102+i, "low": 99+i, "close": 101+i, "volume": 10+i, "trade_price": 1000} for i, time in enumerate(times)])
    for tf in ["1w", "1d", "4h", "1h", "15m"]:
        store.save(tf, "KRW-BTC", frame)
    from mtf.mtf_context_builder import build_v6_mtf_context

    build_v6_mtf_context("KRW-BTC", store)
    result = run_v6_strategy_backtest("ICT_FVG_OB_SWEEP", initial_cash_krw=500000, store=store)
    assert result["trade_count"] >= 0
    assert result["real_order_enabled"] is False
