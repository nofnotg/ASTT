import json

import pandas as pd

from replay_lab.feedback.small_seed_report import SmallSeedReportBuilder


def test_small_seed_report_writes_html_json_markdown_and_docs(tmp_path):
    reports = tmp_path / "reports" / "small_seed_v3"
    reports.mkdir(parents=True)
    (reports / "threshold_sweep_v3.json").write_text(json.dumps({"best": {"status": "NO_VALID_THRESHOLD"}, "rows": []}), encoding="utf-8")
    (reports / "time_window_sweep_v3.json").write_text(json.dumps({"rows": [{"window": "09:00", "entry_count": 1, "risk_adjusted_score": 1.0}]}), encoding="utf-8")
    (reports / "preopen_confirmed_compare_v3.json").write_text(json.dumps({"better_mode": "confirmed", "preopen": {}, "confirmed": {}}), encoding="utf-8")

    exp = tmp_path / "experiments" / "exp_20260101_000000_small_seed_v3"
    exp.mkdir(parents=True)
    (exp / "metrics.json").write_text(json.dumps({"entry_count": 1, "win_rate": 1.0, "total_order_pnl_krw": 100, "account_return_pct": 0.02, "max_drawdown_pct": 0, "profit_factor": 999, "consecutive_loss_max": 0, "live_readiness": "LIVE_NOT_ALLOWED"}), encoding="utf-8")
    pd.DataFrame([{"date_kst": "2026-01-01", "entries": 1, "wins": 1, "losses": 0, "order_pnl_krw": 100, "daily_account_pnl_pct": 0.02, "drawdown_pct": 0}]).to_parquet(exp / "daily_account.parquet", index=False)
    pd.DataFrame([{"period": "2025-12-29", "entries": 1, "win_rate": 1.0, "order_pnl_krw": 100, "account_return_pct": 0.02, "max_drawdown_pct": 0}]).to_parquet(exp / "weekly_account.parquet", index=False)
    pd.DataFrame([{"period": "2026-01-01", "entries": 1, "win_rate": 1.0, "order_pnl_krw": 100, "account_return_pct": 0.02, "max_drawdown_pct": 0}]).to_parquet(exp / "monthly_account.parquet", index=False)
    pd.DataFrame([{"date_kst": "2026-01-01", "market": "KRW-BTC", "order_pnl_krw": 100}]).to_parquet(exp / "paper_trades.parquet", index=False)

    builder = SmallSeedReportBuilder(store_dir=tmp_path, capital_krw=500000, order_krw=10000, docs_root=tmp_path / "docs" / "reports")
    out = builder.build("2026-01-01", "2026-01-01")

    assert out.exists()
    assert (reports / "small_seed_v3_report.json").exists()
    assert (reports / "small_seed_v3_report.md").exists()
    assert "live_readiness" in (builder.docs_dir / "latest_small_seed_summary.json").read_text(encoding="utf-8")
    assert (builder.docs_dir / "latest_small_seed_report.md").exists()
