from pathlib import Path

import pandas as pd

from replay_lab.feedback.report_catalog import ReplayReportCatalog


def test_report_catalog_builds_daily_weekly_monthly(tmp_path):
    exp_dir = tmp_path / "experiments" / "exp_test"
    exp_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"date_kst": "2026-05-08", "market": "KRW-BTC", "vetoed": False},
            {"date_kst": "2026-05-09", "market": "KRW-ETH", "vetoed": True},
        ]
    ).to_parquet(exp_dir / "decisions.parquet", index=False)
    pd.DataFrame(
        [
            {"date_kst": "2026-05-08", "market": "KRW-BTC", "pnl_pct": 1.2},
            {"date_kst": "2026-05-09", "market": "KRW-ETH", "pnl_pct": -0.4},
        ]
    ).to_parquet(exp_dir / "paper_trades.parquet", index=False)
    pd.DataFrame(
        [
            {"date_kst": "2026-05-08", "market": "KRW-BTC"},
            {"date_kst": "2026-05-09", "market": "KRW-ETH"},
        ]
    ).to_parquet(exp_dir / "session_results.parquet", index=False)

    catalog = ReplayReportCatalog(tmp_path).build()

    assert len(catalog["daily"]) == 2
    assert len(catalog["weekly"]) == 1
    assert len(catalog["monthly"]) == 1
    assert catalog["monthly"][0]["entries"] == 2
    assert catalog["insights"]["summary"]["total_entries"] == 2
    assert catalog["insights"]["potential"]
    assert catalog["insights"]["limits"]
    assert catalog["insights"]["developments"]
    assert catalog["insights"]["improvement_insights"]
    assert (tmp_path / "reports" / "catalog" / "daily_replay_report.md").exists()
    assert (tmp_path / "reports" / "catalog" / "replay_insight_report.md").exists()
    html = (tmp_path / "reports" / "catalog" / "replay_report.html").read_text(encoding="utf-8")
    assert "<html lang=\"ko\">" in html
    assert "앱의 가능성" in html
