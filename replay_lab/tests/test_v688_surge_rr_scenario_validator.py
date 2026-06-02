from __future__ import annotations

from analysis.v688_surge_rr_scenario_validator import _select_rules, _simulate_walk_forward, run_v688_surge_rr_scenario_validation


def test_v688_selects_profitable_surge_rr_rules() -> None:
    rows = [
        _row("2026-01-01", 1000, "ALT_FRIENDLY", 1.3, 6.0, -1.0, "ENTER_FULL"),
        _row("2026-01-02", 900, "ALT_FRIENDLY", 1.4, 6.0, -1.0, "ENTER_FULL"),
        _row("2026-01-03", 800, "ALT_FRIENDLY", 1.5, 6.0, -1.0, "ENTER_FULL"),
        _row("2026-01-04", 700, "ALT_FRIENDLY", 1.6, 6.0, -1.0, "ENTER_FULL"),
        _row("2026-01-05", -100, "ALT_FRIENDLY", 1.7, 6.0, -1.0, "ENTER_FULL"),
        _row("2026-01-06", -100, "ALT_FRIENDLY", 1.8, 6.0, -1.0, "ENTER_FULL"),
        _row("2026-02-01", 500, "ALT_FRIENDLY", 1.4, 6.0, -1.0, "ENTER_FULL"),
        _row("2026-02-02", -500, "RISK_OFF_ALT_WEAK", 0.5, -2.0, -12.0, "ENTER_REDUCED_35"),
    ]
    rules = {"2026-02": _select_rules(rows[:6], "SRR_AGGRESSIVE_WF")}

    journal = _simulate_walk_forward("SRR_AGGRESSIVE_WF", rows[6:], 500000.0, rules)

    assert journal[0]["defense_action"] == "ENTER"
    assert journal[1]["defense_action"] == "SKIP"
    assert journal[-1]["equity_after"] > 500000.0


def test_v688_payload_is_paper_locked(tmp_path) -> None:
    reports = tmp_path / "reports"
    data = tmp_path / "data"
    journal = data / "journal"
    reports.mkdir(parents=True)
    journal.mkdir(parents=True)
    (reports / "latest_v683_backfill_20260101_summary.json").write_text(
        '{"run_id":"r1","active_route":"ACTIVE","routes":[{"scenario":"ACTIVE","return_pct":0,"mdd_pct":0}]}',
        encoding="utf-8",
    )
    trade_lines = []
    decision_lines = []
    for idx, pnl in enumerate([1000, 900, 800, 700, -100, -100, 500], start=1):
        day = f"2026-01-{idx:02d}" if idx <= 6 else "2026-02-01"
        trade_id = f"r1:t{idx}"
        trade_lines.append(
            f'{{"trade_id":"{trade_id}","entry_time":"{day} 01:00:00","exit_time":"{day} 02:00:00","market":"KRW-BTC","size_krw":100000,"realized_pnl_krw":{pnl},"pnl_pct":1.0,"real_order_enabled":false,"live_order_allowed":false,"auto_apply_allowed":false}}'
        )
        decision_lines.append(
            f'{{"decision_id":"{trade_id}","decision_time":"{day} 01:00:00","market_state":"ALT_FRIENDLY","action":"ENTER_FULL","dominance_risk":false,"pf20":1.5,"month_return_pct":6,"hwm_drawdown_pct":-1,"reason":["NO_DEFENSE"],"real_order_enabled":false,"live_order_allowed":false,"auto_apply_allowed":false}}'
        )
    (journal / "paper_trades.jsonl").write_text("\n".join(trade_lines), encoding="utf-8")
    (journal / "paper_decisions.jsonl").write_text("\n".join(decision_lines), encoding="utf-8")

    payload = run_v688_surge_rr_scenario_validation(reports_dir=reports, data_dir=data)

    assert payload["real_order_enabled"] is False
    assert payload["routes"]
    assert (reports / "latest_v688_surge_rr_scenario_summary.json").exists()


def _row(date: str, pnl: float, state: str, pf20: float, month_return: float, dd: float, action: str) -> dict:
    return {
        "date": date,
        "month": date[:7],
        "time": f"{date} 01:00:00",
        "entry_time": f"{date} 01:00:00",
        "exit_time": f"{date} 02:00:00",
        "market": "KRW-BTC",
        "size_krw": 100000.0,
        "pnl_krw": pnl,
        "pnl_pct": pnl / 1000.0,
        "market_state": state,
        "dominance_risk": state != "ALT_FRIENDLY",
        "pf20": pf20,
        "month_return_pct": month_return,
        "hwm_drawdown_pct": dd,
        "action": action,
        "reason": ["NO_DEFENSE"],
    }
