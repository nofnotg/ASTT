import pytest

from replay_lab.research.small_seed_metrics import aggregate_small_seed_daily, calc_trade_pnl


def test_calc_trade_pnl_splits_signal_order_and_account_pnl():
    gross = calc_trade_pnl(500000, 10000, 1.0, fee_pct=0.0, slippage_pct=0.0)
    assert gross["order_pnl_krw"] == pytest.approx(100.0)
    assert gross["account_pnl_pct"] == pytest.approx(0.02)

    net = calc_trade_pnl(500000, 10000, 1.0)
    assert net["net_signal_pnl_pct"] == pytest.approx(0.75)
    assert net["order_pnl_krw"] == pytest.approx(75.0)


def test_aggregate_daily_tracks_account_drawdown():
    daily = aggregate_small_seed_daily(
        [
            {"date_kst": "2026-01-01", "entered": True, "order_pnl_krw": 100, "gross_signal_pnl_pct": 1, "net_signal_pnl_pct": 1},
            {"date_kst": "2026-01-02", "entered": True, "order_pnl_krw": -200, "gross_signal_pnl_pct": -2, "net_signal_pnl_pct": -2},
        ],
        capital_krw=500000,
    )
    assert len(daily) == 2
    assert daily.iloc[1]["drawdown_pct"] < 0
