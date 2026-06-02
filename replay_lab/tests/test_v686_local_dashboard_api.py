from __future__ import annotations

from local_dashboard.dashboard_data_service import DashboardDataService


def test_v686_dashboard_api_returns_health_and_routes(tmp_path) -> None:
    reports = tmp_path
    (reports / "latest_v686_active_shadow_runtime_summary.json").write_text('{"active_route":"LG_V2_BALANCED_PLUS_DOM_GATE","routes":[]}', encoding="utf-8")
    service = DashboardDataService(str(reports))
    assert service.health()["dashboard_ready"] is True
    assert service.routes()["active_route"] == "LG_V2_BALANCED_PLUS_DOM_GATE"


def test_v686_dashboard_api_returns_investment_records(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_v683_backfill_20260101_summary.json").write_text(
        """
        {
          "mode":"PAPER_ONLY",
          "start_date":"2026-01-01",
          "active_route":"LG_V2_BALANCED_PLUS_DOM_GATE",
          "daily_equity":{
            "LG_V2_BALANCED_PLUS_DOM_GATE":[{"period":"2026-01-02","pnl_krw":1000,"return_pct":1.0}],
            "SHADOW":[{"period":"2026-01-03","pnl_krw":2000,"return_pct":2.0}]
          },
          "weekly_returns":{
            "LG_V2_BALANCED_PLUS_DOM_GATE":[{"period":"2026-W01","pnl_krw":1000,"return_pct":1.0}],
            "SHADOW":[{"period":"2026-W01","pnl_krw":2000,"return_pct":2.0}]
          },
          "monthly_returns":{
            "LG_V2_BALANCED_PLUS_DOM_GATE":[{"period":"2026-01","pnl_krw":1000,"return_pct":1.0}],
            "SHADOW":[{"period":"2026-01","pnl_krw":2000,"return_pct":2.0}]
          },
          "routes":[
            {"scenario":"LG_V2_BALANCED_PLUS_DOM_GATE","route_status":"ACTIVE","return_pct":1.0,"mdd_pct":-5.0},
            {"scenario":"SHADOW","route_status":"SHADOW","return_pct":2.0,"mdd_pct":-4.0}
          ]
        }
        """,
        encoding="utf-8",
    )
    service = DashboardDataService(str(reports), str(tmp_path / "data"))
    records = service.investment_records()
    assert records["start_date"] == "2026-01-01"
    assert records["scenario_policy"]["investment_start_date"] == "2026-01-01"
    assert records["scenario_policy"]["primary_route"] == "SHADOW"
    assert records["scenario_policy"]["max_maintained_routes"] == 5
    assert len(records["routes"]) <= 5
    assert records["monthly"][0]["month"] == "2026-01"
    assert records["active_route"] == "SHADOW"
    assert records["previous_runtime_active_route"] == "LG_V2_BALANCED_PLUS_DOM_GATE"
    assert records["monthly"][0]["route_label"] == "SHADOW"
    assert records["weekly"][0]["month"] == "2026-01"
    assert [row["period"] for row in records["daily"]] == ["2026-01-03", "2026-01-02", "2026-01-01"]
    assert records["daily"][0]["week"] == "2026-W01"
    assert records["daily"][1]["result"] == "거래없음"
    assert records["daily"][1]["trade_count"] == 0
    assert "체결 없음" in records["daily"][1]["trade_comment"]
    assert records["monthly_by_route"][0]["result"] == "수익"
    assert records["monthly_by_route"][0]["comparison_rank"] == "best"
    assert records["latest_record_date"] == "2026-01-03"
    assert records["record_staleness"]["status"] in {"FRESH", "STALE"}
    assert records["route_agent_recommendation"]["recommended_route"] == "SHADOW"
    assert records["route_agent_recommendation"]["auto_apply_allowed"] is False


def test_v686_dashboard_api_returns_investment_logs(tmp_path) -> None:
    data_dir = tmp_path / "data"
    journal = data_dir / "journal"
    journal.mkdir(parents=True)
    (journal / "paper_trades.jsonl").write_text(
        '{"trade_id":"t1","route_id":"R1","route_status":"ACTIVE","market":"KRW-BTC","entry_time":"2026-01-02 01:00:00","exit_time":"2026-01-02 02:00:00","size_krw":10000,"realized_pnl_krw":500,"pnl_pct":5,"exit_reason":"TARGET","real_order_enabled":false,"live_order_allowed":false,"auto_apply_allowed":false}\n',
        encoding="utf-8",
    )
    (journal / "paper_decisions.jsonl").write_text(
        '{"decision_time":"2026-01-02 01:00:00","route_id":"R1","market":"KRW-BTC","action":"ENTER","guard_on":true,"dominance_risk":false,"real_order_enabled":false,"live_order_allowed":false,"auto_apply_allowed":false}\n',
        encoding="utf-8",
    )
    service = DashboardDataService(str(tmp_path / "reports"), str(data_dir))
    logs = service.investment_logs()
    assert [row["action"] for row in logs["trade_logs"]] == ["매도/청산", "매수"]
    assert logs["scenario_logs"][0]["action"] == "ENTER"
    assert logs["live_order_allowed"] is False
