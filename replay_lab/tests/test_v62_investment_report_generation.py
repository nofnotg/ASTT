from __future__ import annotations

from replay_lab.research.v62_capital_growth_backtest import run_v62_capital_growth_backtest


def test_v62_capital_growth_backtest_writes_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_v62_capital_growth_backtest(500000, True, True)
    assert result["real_order_enabled"] is False
    assert (tmp_path / "docs/reports/latest_v62_full_investment_summary.json").exists()
