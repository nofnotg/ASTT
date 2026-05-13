import pandas as pd

from replay_lab.feedback.report_catalog import ReplayReportCatalog


def test_report_catalog_builds_daily_weekly_monthly(tmp_path):
    exp_dir = tmp_path / "experiments" / "exp_test"
    exp_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"date_kst": "2026-05-08", "market": "KRW-BTC", "vetoed": False, "entry_time_kst": "2026-05-08T09:00:00", "day_type": "weekday"},
            {"date_kst": "2026-05-09", "market": "KRW-ETH", "vetoed": True, "entry_time_kst": "2026-05-09T09:00:00", "day_type": "weekend"},
        ]
    ).to_parquet(exp_dir / "decisions.parquet", index=False)
    pd.DataFrame(
        [
            {"date_kst": "2026-05-08", "market": "KRW-BTC", "pnl_pct": 1.2, "entry_time_kst": "2026-05-08T09:00:00", "day_type": "weekday"},
            {"date_kst": "2026-05-09", "market": "KRW-ETH", "pnl_pct": -0.4, "entry_time_kst": "2026-05-09T09:00:00", "day_type": "weekend"},
        ]
    ).to_parquet(exp_dir / "paper_trades.parquet", index=False)
    pd.DataFrame(
        [
            {"date_kst": "2026-05-08", "market": "KRW-BTC"},
            {"date_kst": "2026-05-09", "market": "KRW-ETH"},
        ]
    ).to_parquet(exp_dir / "session_results.parquet", index=False)
    pd.DataFrame(
        [
            {"session_id": "s1", "date_kst": "2026-05-08", "market": "KRW-BTC", "persona": "Mr.K", "score": 72, "decision": "PASS", "veto": False},
            {"session_id": "s1", "date_kst": "2026-05-08", "market": "KRW-BTC", "persona": "Rezo", "score": 88, "decision": "PASS", "veto": False},
            {"session_id": "s2", "date_kst": "2026-05-09", "market": "KRW-ETH", "persona": "Mr.K", "score": 55, "decision": "REJECT", "veto": False},
            {"session_id": "s2", "date_kst": "2026-05-09", "market": "KRW-ETH", "persona": "Iris", "score": 85, "decision": "PASS", "veto": False},
        ]
    ).to_parquet(exp_dir / "persona_scores.parquet", index=False)

    catalog = ReplayReportCatalog(tmp_path, capital_krw=500000).build()

    assert len(catalog["daily"]) == 2
    assert len(catalog["weekly"]) == 1
    assert len(catalog["monthly"]) == 1
    assert len(catalog["time_windows"]) == 2
    assert len(catalog["persona_validity"]) == 3
    assert len(catalog["macro_persona_context"]) == 5
    assert catalog["monthly"][0]["entries"] == 2
    assert catalog["insights"]["summary"]["total_entries"] == 2
    assert catalog["insights"]["summary"]["portfolio_pnl_krw"] == 4000
    assert catalog["insights"]["potential"]
    assert catalog["insights"]["limits"]
    assert catalog["insights"]["developments"]
    assert catalog["insights"]["improvement_insights"]
    assert (tmp_path / "reports" / "catalog" / "daily_replay_report.md").exists()
    assert (tmp_path / "reports" / "catalog" / "replay_insight_report.md").exists()
    html = (tmp_path / "reports" / "catalog" / "replay_report.html").read_text(encoding="utf-8")
    assert "<html lang=\"ko\">" in html
    assert "앱의 가능성" in html
    assert "쉬운 용어 해설" in html
    assert "페르소나 유효성 검증" in html
    assert "거시/국내정세와 페르소나 연결 검토" in html
