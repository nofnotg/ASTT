from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from local_dashboard.dashboard_security import security_status
from paper_runtime.paper_runtime_schema import safety_flags


ROUTE_ALIASES = {
    "LG_V2_BALANCED_PLUS_DOM_GATE": "LGv2-DOM",
    "LG_M3_PF0.8_DD8": "LG-M3",
    "LOSS_GUARD_2026_ROUTER_V1_SHADOW": "LG-Router",
    "BASE_BALANCED": "Balanced",
    "BASE_ROLLING": "Rolling",
    "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW": "Bear-V685",
    "BEAR_ROUTER_V684_SHADOW": "Bear-V684",
    "LG_COMBINED_GUARD": "LG-Combo",
    "SRR_STRICT_WF": "SRR-S",
    "SRR_BALANCED_WF": "SRR-B",
    "SRR_AGGRESSIVE_WF": "SRR-A",
    "SRR_STRICT_ORACLE": "SRR-S-O",
    "SRR_BALANCED_ORACLE": "SRR-B-O",
    "SRR_AGGRESSIVE_ORACLE": "SRR-A-O",
}


class DashboardDataService:
    def __init__(
        self,
        reports_dir: str = "docs/reports",
        data_dir: str = "data/paper",
        forward_dir: str = "replay_store/sessions/forward_ws_v554",
    ) -> None:
        self.reports = Path(reports_dir)
        self.data = Path(data_dir)
        self.forward_dir = Path(forward_dir)

    def health(self) -> dict[str, Any]:
        local = self._read("latest_v686_local_dashboard_summary.json")
        return {
            "status": "PASS",
            "dashboard_ready": True,
            "paper_runtime_connected": bool(self._read("latest_v686_active_shadow_runtime_summary.json")),
            "reports_dir": str(self.reports),
            **local,
            **security_status(),
        }

    def account(self) -> dict[str, Any]:
        runtime = self._read("latest_v686_active_shadow_runtime_summary.json") or self._read("latest_v683_paper_runtime_summary.json")
        active = next((row for row in runtime.get("routes", []) if row.get("route_status") == "ACTIVE"), {})
        return {
            "active_route": runtime.get("active_route") or active.get("scenario"),
            "current_equity_krw": active.get("final_equity_krw", runtime.get("current_equity_krw", 0.0)),
            "current_cash_krw": active.get("final_equity_krw", runtime.get("current_cash_krw", 0.0)),
            "open_positions": runtime.get("open_positions", 0),
            "today_pnl_krw": runtime.get("today_pnl_krw", 0.0),
            "weekly_pnl_krw": runtime.get("weekly_pnl_krw", 0.0),
            "monthly_pnl_krw": runtime.get("monthly_pnl_krw", 0.0),
            **safety_flags(),
        }

    def routes(self) -> dict[str, Any]:
        runtime = self._read("latest_v686_active_shadow_runtime_summary.json")
        registration = self._read("latest_v686_shadow_route_registration_summary.json")
        return {
            "active_route": runtime.get("active_route", registration.get("active_route")),
            "shadow_routes": registration.get("shadow_routes", runtime.get("shadow_routes", [])),
            "research_shadow_routes": registration.get("research_shadow_routes", []),
            "route_switch_locked": True,
            "active_auto_switch_allowed": False,
            "rows": runtime.get("routes", []),
            **safety_flags(),
        }

    def positions(self) -> dict[str, Any]:
        return {"open_positions": [], "count": 0, **safety_flags()}

    def trades(self, limit: int = 100) -> dict[str, Any]:
        return {"rows": self._read_jsonl(self.data / "journal" / "paper_trades.jsonl", limit), **safety_flags()}

    def decisions(self, limit: int = 100) -> dict[str, Any]:
        return {"rows": self._read_jsonl(self.data / "journal" / "paper_decisions.jsonl", limit), **safety_flags()}

    def investment_records(self) -> dict[str, Any]:
        backfill = self._read("latest_v683_backfill_20260101_summary.json")
        surge_rr = self._read("latest_v688_surge_rr_scenario_summary.json")
        runtime = self._read("latest_v686_active_shadow_runtime_summary.json")
        scenario_decision = self._read("latest_v689_scenario_decision_summary.json")
        active_route = backfill.get("active_route") or runtime.get("active_route")
        routes = self._merge_routes(backfill.get("routes", []), runtime.get("routes", []), surge_rr.get("routes", []))
        policy = self._scenario_policy(routes, active_route, backfill)
        primary_route = policy.get("primary_route") or active_route
        daily = self._period_rows(backfill.get("daily_equity", {}).get(primary_route, []), primary_route, "daily")
        latest_record_date = max((str(row.get("period", "")) for row in daily), default=None)
        daily = self._fill_daily_calendar(
            daily,
            route_id=primary_route,
            start_date=str(backfill.get("start_date", "2026-01-01")),
            end_date=latest_record_date,
            initial_cash_krw=float(backfill.get("initial_cash_krw", 0.0) or 0.0),
        )
        weekly = self._period_rows(backfill.get("weekly_returns", {}).get(primary_route, []), primary_route, "weekly")
        monthly = self._period_rows(backfill.get("monthly_returns", {}).get(primary_route, []), primary_route, "monthly")
        forward_logs = self._forward_candidate_logs()
        forward_daily = self._forward_daily_calendar(forward_logs)
        daily = self._combined_daily_trade_calendar(daily, forward_daily)
        weekly = self._extend_period_rows_from_daily(weekly, daily, latest_record_date, "weekly")
        monthly = self._extend_period_rows_from_daily(monthly, daily, latest_record_date, "monthly")
        latest_display_record_date = max((str(row.get("period", ""))[:10] for row in daily if row.get("period")), default=latest_record_date)
        monthly_by_route: list[dict[str, Any]] = []
        for route_id, rows in backfill.get("monthly_returns", {}).items():
            monthly_by_route.extend(self._period_rows(rows, route_id, "monthly"))
        for route_id, rows in surge_rr.get("monthly_returns", {}).items():
            monthly_by_route.extend(self._period_rows(rows, route_id, "monthly"))
        return {
            "mode": backfill.get("mode", "PAPER_ONLY"),
            "source_mode": backfill.get("source_mode", "historical_backfill"),
            "start_date": backfill.get("start_date", "2026-01-01"),
            "initial_cash_krw": backfill.get("initial_cash_krw", 0.0),
            "active_route": primary_route,
            "previous_runtime_active_route": active_route if primary_route != active_route else None,
            "route_aliases": ROUTE_ALIASES,
            "scenario_policy": policy,
            "routes": policy["maintained_routes"],
            "research_routes": policy["research_routes"],
            "route_agent_recommendation": policy["route_agent_recommendation"],
            "scenario_decision": scenario_decision,
            "operating_summary": scenario_decision.get("operating_summary", {}),
            "plain_conclusion": scenario_decision.get("conclusion", {}),
            "monthly": list(reversed(monthly)),
            "weekly": list(reversed(weekly)),
            "daily": daily,
            "monthly_by_route": list(reversed(self._rank_monthly_routes(monthly_by_route))),
            "latest_record_date": latest_display_record_date,
            "historical_latest_record_date": latest_record_date,
            "record_staleness": self._record_staleness(latest_display_record_date),
            "latest_market_data": self._latest_market_data(),
            "latest_forward_ws": self._latest_forward_ws(),
            **safety_flags(),
        }

    def investment_logs(self, limit: int = 2000) -> dict[str, Any]:
        trades = self._read_jsonl(self.data / "journal" / "paper_trades.jsonl", limit)
        decisions = self._read_jsonl(self.data / "journal" / "paper_decisions.jsonl", limit)
        records = self.investment_records()
        forward_logs = self._forward_candidate_logs()
        forward_daily = self._forward_daily_calendar(forward_logs)
        return {
            "forward_daily_calendar": forward_daily,
            "forward_candidate_logs": forward_logs,
            "daily_trade_calendar": self._combined_daily_trade_calendar(records.get("daily", []), forward_daily),
            "trade_logs": self._trade_logs(trades),
            "scenario_logs": self._scenario_logs(decisions),
            **safety_flags(),
        }

    def active_shadow(self) -> dict[str, Any]:
        return self._read("latest_v686_active_shadow_runtime_summary.json")

    def bear_windows(self) -> dict[str, Any]:
        return self._read("latest_v686_bear_window_atr_replay_summary.json") or self._read("latest_v685_bear_window_performance_summary.json")

    def atr_research(self) -> dict[str, Any]:
        return {
            "coverage": self._read("latest_v686_atr_ltf_coverage_summary.json"),
            "precision": self._read("latest_v686_atr_precision_v2_summary.json"),
            "model_comparison": self._read("latest_v686_atr_model_comparison_summary.json"),
            **safety_flags(),
        }

    def control_tower(self) -> dict[str, Any]:
        return self._read("latest_v686_control_tower_dashboard_summary.json")

    def v688_dashboard(self) -> dict[str, Any]:
        dashboard = self._read("latest_v688_control_tower_dashboard_summary.json")
        active_analysis = self._read("latest_v688_active_analysis_recommendations_summary.json")
        return {
            "dashboard": dashboard,
            "scenario_genome": self._read("latest_v688_scenario_genome_summary.json"),
            "scenario_daily": self._read("latest_v688_scenario_daily_summary.json"),
            "scenario_weekly": self._read("latest_v688_scenario_weekly_summary.json"),
            "scenario_monthly": self._read("latest_v688_scenario_monthly_summary.json"),
            "disagreement": self._read("latest_v688_scenario_disagreement_summary.json"),
            "missed_opportunity": self._read("latest_v688_missed_opportunity_summary.json"),
            "profit_giveback": self._read("latest_v688_profit_giveback_summary.json"),
            "variable_convergence": self._read("latest_v688_variable_convergence_summary.json"),
            "active_analysis": active_analysis,
            "llm_daily": self._read("latest_v688_llm_daily_review_summary.json"),
            "llm_weekly": self._read("latest_v688_llm_weekly_council_summary.json"),
            "llm_monthly": self._read("latest_v688_llm_monthly_deck_review_summary.json"),
            "tabs": dashboard.get("tabs", {}),
            "route_state": active_analysis.get("route_state", dashboard.get("scenario_genome", {}).get("route_state", {})),
            "active_change_applied": False,
            "active_route_change_applied": False,
            "llm_active_change_applied": False,
            "manual_review_required": True,
            "order_api_called": False,
            **safety_flags(),
        }

    def v690_dashboard(self) -> dict[str, Any]:
        return {
            "loop": self._read("latest_v690_scenario_improvement_loop_summary.json"),
            "decomposition": self._read("latest_v690_2026_scenario_decomposition_summary.json"),
            "failure_signature": self._read("latest_v690_failure_signature_summary.json"),
            "giveback_missed": self._read("latest_v690_giveback_missed_opportunity_summary.json"),
            "candidates": self._read("latest_v690_improved_scenario_candidates_summary.json"),
            "backtest_2026": self._read("latest_v690_2026_improvement_backtest_summary.json"),
            "full_period_safety": self._read("latest_v690_full_period_safety_summary.json"),
            "decision": self._read("latest_v690_improvement_decision_summary.json"),
            "llm_review": self._read("latest_v690_improvement_llm_review_summary.json"),
            "active_change_applied": False,
            "active_route_change_applied": False,
            "llm_active_change_applied": False,
            "manual_review_required": True,
            "order_api_called": False,
            **safety_flags(),
        }

    def v691_dashboard(self) -> dict[str, Any]:
        return {
            "loop": self._read("latest_v691_vwap_pressure_feature_lab_summary.json"),
            "features": self._read("latest_v691_vwap_feature_summary.json"),
            "effectiveness": self._read("latest_v691_vwap_indicator_effectiveness_summary.json"),
            "candidates": self._read("latest_v691_vwap_scenario_candidates_summary.json"),
            "backtest_2026": self._read("latest_v691_2026_vwap_scenario_backtest_summary.json"),
            "drawdown": self._read("latest_v691_drawdown_reduction_summary.json"),
            "full_period_safety": self._read("latest_v691_full_period_vwap_safety_summary.json"),
            "decision": self._read("latest_v691_vwap_decision_summary.json"),
            "llm_review": self._read("latest_v691_vwap_llm_review_summary.json"),
            "active_change_applied": False,
            "active_route_change_applied": False,
            "llm_active_change_applied": False,
            "manual_review_required": True,
            "order_api_called": False,
            **safety_flags(),
        }

    def pattern_validation(self) -> dict[str, Any]:
        payload = self._read("latest_v687_investment_pattern_validation_summary.json")
        surge_rr = self._read("latest_v688_surge_rr_scenario_summary.json")
        for key in ("routes", "oracle_reference_routes"):
            surge_rr[key] = [{**row, "scenario_label": self._alias(row.get("scenario"))} for row in surge_rr.get(key, [])]
        payload["surge_rr_scenario"] = surge_rr
        return payload

    def _read(self, name: str) -> dict[str, Any]:
        path = self.reports / name
        return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}

    def _read_jsonl(self, path: Path, limit: int) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        rows = []
        for line in lines[-limit:]:
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def _latest_market_data(self) -> dict[str, Any]:
        summary = self._read("latest_historical_archive_summary.json")
        latest = summary.get("latest_time")
        today = date.today()
        bounded = []
        for row in summary.get("rows", []):
            if row.get("timeframe") == "1w" or not row.get("latest_time"):
                continue
            try:
                parsed = datetime.fromisoformat(str(row["latest_time"])).date()
            except ValueError:
                continue
            if parsed <= today:
                bounded.append(str(row["latest_time"]))
        if bounded:
            latest = max(bounded)
        return {
            "latest_time": latest,
            "market_count": summary.get("market_count"),
            "missing_market_count": summary.get("missing_market_count"),
        }

    def _latest_forward_ws(self) -> dict[str, Any]:
        root = self.forward_dir
        marker = root / "live_forward_process.json"
        row, _ = self._latest_forward_session()
        running = {}
        if marker.exists():
            try:
                running = json.loads(marker.read_text(encoding="utf-8-sig"))
                started = datetime.fromisoformat(str(running.get("started_at")))
                duration = int(running.get("duration_minutes", 0) or 0)
                if datetime.utcnow() <= started + timedelta(minutes=duration):
                    running["status"] = "RUNNING"
            except (ValueError, TypeError, json.JSONDecodeError):
                running = {}
        if not row:
            return running or {"status": "NO_FORWARD_WS_SESSION"}
        timestamp = self._forward_timestamp(row)
        latest = {
            "session_id": row.get("session_id"),
            "status": row.get("status"),
            "started_at": row.get("source_session", {}).get("started_at"),
            "ended_at": timestamp,
            "duration_minutes": row.get("duration_minutes"),
            "trade_event_count": row.get("trade_event_count"),
            "orderbook_event_count": row.get("orderbook_event_count"),
            "candidate_count": row.get("candidate_count"),
            "enter_count": row.get("enter_count"),
            "wait_count": row.get("wait_count"),
            "block_reason_counts": row.get("block_reason_counts", {}),
            "real_order_enabled": row.get("real_order_enabled", False),
            "live_order_allowed": False,
            "auto_apply_allowed": False,
            "source_mode": "forward_paper_ws",
        }
        if running.get("status") == "RUNNING":
            return {**latest, **running, "last_completed_session_id": latest.get("session_id"), "last_completed_candidate_count": latest.get("candidate_count")}
        return latest

    def _latest_forward_session(self) -> tuple[dict[str, Any], Path | None]:
        files = sorted(self.forward_dir.glob("*/session_summary.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        for path in files:
            try:
                row = json.loads(path.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row.get("session_id"):
                return row, path
        return {}, None

    def _forward_timestamp(self, session: dict[str, Any]) -> str | None:
        source = session.get("source_session", {}) if isinstance(session.get("source_session"), dict) else {}
        return (
            session.get("ended_at")
            or source.get("ended_at")
            or session.get("started_at")
            or source.get("started_at")
        )

    def _forward_candidate_events(self, session: dict[str, Any], summary_path: Path | None) -> list[dict[str, Any]]:
        embedded = session.get("candidate_events")
        if isinstance(embedded, list):
            return [row for row in embedded if isinstance(row, dict)]
        if not summary_path:
            return []
        path = summary_path.parent / "candidate_events.json"
        if not path.exists():
            return []
        try:
            rows = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            return []
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    def _forward_candidate_logs(self) -> list[dict[str, Any]]:
        session, summary_path = self._latest_forward_session()
        if not session:
            return []
        timestamp = self._forward_timestamp(session) or ""
        period = timestamp[:10] if timestamp else ""
        events = self._forward_candidate_events(session, summary_path)
        logs = []
        for index, event in enumerate(events, start=1):
            decision = str(event.get("entry_decision") or "WAIT")
            reason = str(event.get("primary_block_reason") or "-")
            result = "거래없음" if decision == "WAIT" else "진입" if decision == "ENTER" else decision
            action = "관찰대기" if decision == "WAIT" else decision
            comment = (
                f"실시간 후보는 있었지만 {reason}로 진입 조건 약함. paper 거래 없음."
                if decision == "WAIT"
                else "Forward paper 조건 충족 후보."
            )
            logs.append(
                {
                    "period": period,
                    "time": timestamp,
                    "session_id": session.get("session_id"),
                    "source_mode": "forward_paper_ws",
                    "candidate_index": index,
                    "market": event.get("market"),
                    "strategy_id": event.get("strategy_id"),
                    "action": action,
                    "entry_decision": decision,
                    "result": result,
                    "primary_block_reason": reason,
                    "trade_event_count": event.get("trade_event_count"),
                    "orderbook_event_count": event.get("orderbook_event_count"),
                    "orderbook_available": event.get("orderbook_available"),
                    "trade_comment": comment,
                    "real_order_enabled": bool(session.get("real_order_enabled", False)),
                    "live_order_allowed": False,
                    "auto_apply_allowed": False,
                }
            )
        return sorted(logs, key=lambda item: (str(item.get("time", "")), int(item.get("candidate_index", 0))), reverse=True)

    def _forward_daily_calendar(self, logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        session, _ = self._latest_forward_session()
        if not session:
            return []
        timestamp = self._forward_timestamp(session) or ""
        period = timestamp[:10] if timestamp else ""
        candidate_count = int(session.get("candidate_count", len(logs)) or 0)
        enter_count = int(session.get("enter_count", 0) or 0)
        wait_count = int(session.get("wait_count", 0) or 0)
        block_counts = session.get("block_reason_counts", {}) if isinstance(session.get("block_reason_counts"), dict) else {}
        top_reason = max(block_counts, key=block_counts.get) if block_counts else "-"
        result = "거래없음" if enter_count == 0 else "진입있음"
        return [
            {
                "period": period,
                "time": timestamp,
                "route_label": "Forward",
                "source_mode": "forward_paper_ws",
                "candidate_count": candidate_count,
                "enter_count": enter_count,
                "wait_count": wait_count,
                "trade_count": enter_count,
                "result": result,
                "primary_block_reason": top_reason,
                "trade_comment": f"Forward 후보 {candidate_count}건, 진입 {enter_count}건, 대기 {wait_count}건. 주 사유: {top_reason}.",
                "real_order_enabled": bool(session.get("real_order_enabled", False)),
                "live_order_allowed": False,
                "auto_apply_allowed": False,
            }
        ]

    def _combined_daily_trade_calendar(self, daily_rows: list[dict[str, Any]], forward_daily: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_day = {str(row.get("period", ""))[:10]: dict(row) for row in daily_rows if row.get("period")}
        forward_by_day = {str(row.get("period", ""))[:10]: row for row in forward_daily if row.get("period")}
        if not by_day and not forward_by_day:
            return []
        if not forward_by_day:
            return sorted(by_day.values(), key=lambda item: str(item.get("period", "")), reverse=True)

        valid_existing_dates = []
        for period in by_day:
            try:
                valid_existing_dates.append(date.fromisoformat(period))
            except ValueError:
                continue
        valid_forward_dates = []
        for period in forward_by_day:
            try:
                valid_forward_dates.append(date.fromisoformat(period))
            except ValueError:
                continue

        if valid_existing_dates:
            start = max(valid_existing_dates) + timedelta(days=1)
        elif valid_forward_dates:
            start = min(valid_forward_dates)
        else:
            return sorted(by_day.values(), key=lambda item: str(item.get("period", "")), reverse=True)

        end = max([date.today(), *valid_forward_dates] if valid_forward_dates else [date.today()])
        last_equity = self._latest_known_equity(by_day)
        cursor = start
        while cursor <= end:
            period = cursor.isoformat()
            if period not in by_day:
                month, week = self._period_keys(period, "daily")
                by_day[period] = {
                    "period": period,
                    "time": None,
                    "trade_count": 0,
                    "start_equity_krw": last_equity,
                    "end_equity_krw": last_equity,
                    "pnl_krw": 0.0,
                    "return_pct": 0.0,
                    "mdd_pct": None,
                    "route_id": "FORWARD_PAPER",
                    "route_label": "Forward",
                    "kind": "daily",
                    "month": month,
                    "week": week,
                    "source_mode": "forward_paper_calendar",
                    "result": "거래없음",
                    "trade_comment": "백필 체결 기록 없음. Forward 후보 로그 없음. paper 관찰 대기.",
                    "real_order_enabled": False,
                    "live_order_allowed": False,
                    "auto_apply_allowed": False,
                }
            cursor += timedelta(days=1)

        for period, forward in forward_by_day.items():
            month, week = self._period_keys(period, "daily")
            base = by_day.get(period, {})
            equity = float(base.get("end_equity_krw", base.get("start_equity_krw", last_equity)) or last_equity)
            by_day[period] = {
                **base,
                **forward,
                "route_id": "FORWARD_PAPER",
                "route_label": "Forward",
                "kind": "daily",
                "month": month,
                "week": week,
                "start_equity_krw": base.get("start_equity_krw", equity),
                "end_equity_krw": base.get("end_equity_krw", equity),
                "pnl_krw": base.get("pnl_krw", 0.0),
                "return_pct": base.get("return_pct", 0.0),
                "mdd_pct": base.get("mdd_pct"),
            }
        return sorted(by_day.values(), key=lambda item: str(item.get("period", "")), reverse=True)

    def _latest_known_equity(self, by_day: dict[str, dict[str, Any]]) -> float:
        latest_equity = 0.0
        for period in sorted(by_day):
            row = by_day[period]
            latest_equity = float(row.get("end_equity_krw", row.get("start_equity_krw", latest_equity)) or latest_equity)
        return latest_equity

    def _extend_period_rows_from_daily(
        self,
        period_rows: list[dict[str, Any]],
        daily_rows: list[dict[str, Any]],
        historical_latest_date: str | None,
        kind: str,
    ) -> list[dict[str, Any]]:
        if kind not in {"weekly", "monthly"} or not historical_latest_date:
            return period_rows
        try:
            cutoff = date.fromisoformat(historical_latest_date[:10])
        except ValueError:
            return period_rows

        existing_periods = {str(row.get("period", "")) for row in period_rows}
        groups: dict[str, list[dict[str, Any]]] = {}
        for row in daily_rows:
            period = str(row.get("period", ""))[:10]
            try:
                parsed = date.fromisoformat(period)
            except ValueError:
                continue
            if parsed <= cutoff:
                continue
            group_period = parsed.strftime("%Y-%m") if kind == "monthly" else f"{parsed.isocalendar().year}-W{parsed.isocalendar().week:02d}"
            if group_period in existing_periods:
                continue
            groups.setdefault(group_period, []).append(row)

        additions = [self._aggregate_forward_period(period, rows, kind) for period, rows in sorted(groups.items())]
        return [*period_rows, *additions]

    def _aggregate_forward_period(self, period: str, rows: list[dict[str, Any]], kind: str) -> dict[str, Any]:
        ordered = sorted(rows, key=lambda row: str(row.get("period", "")))
        start_equity = float(ordered[0].get("start_equity_krw", 0.0) or 0.0) if ordered else 0.0
        end_equity = float(ordered[-1].get("end_equity_krw", start_equity) or start_equity) if ordered else start_equity
        pnl = sum(float(row.get("pnl_krw", 0.0) or 0.0) for row in ordered)
        trade_count = sum(int(row.get("trade_count", 0) or 0) for row in ordered)
        candidate_count = sum(int(row.get("candidate_count", 0) or 0) for row in ordered)
        wait_count = sum(int(row.get("wait_count", 0) or 0) for row in ordered)
        reasons = [str(row.get("primary_block_reason")) for row in ordered if row.get("primary_block_reason")]
        primary_reason = reasons[0] if reasons else None
        month, week = self._period_keys(period, kind)
        if candidate_count:
            comment = f"Forward 후보 {candidate_count}건, 진입 {trade_count}건, 대기 {wait_count}건. 주 사유: {primary_reason or '-'}."
        else:
            comment = "백필 체결 기록 없음. Forward 후보 로그 없음. paper 관찰 대기."
        return {
            "period": period,
            "route_id": "FORWARD_PAPER",
            "route_label": "Forward",
            "kind": kind,
            "month": month,
            "week": week,
            "start_equity_krw": start_equity,
            "end_equity_krw": end_equity,
            "pnl_krw": pnl,
            "return_pct": ((end_equity / start_equity) - 1.0) * 100.0 if start_equity else 0.0,
            "mdd_pct": None,
            "trade_count": trade_count,
            "candidate_count": candidate_count or None,
            "wait_count": wait_count or None,
            "result": "수익" if pnl > 0 else "손실" if pnl < 0 else "거래없음",
            "primary_block_reason": primary_reason,
            "trade_comment": comment,
            "source_mode": "forward_paper_calendar",
            "real_order_enabled": False,
            "live_order_allowed": False,
            "auto_apply_allowed": False,
        }

    def _period_rows(self, rows: list[dict[str, Any]], route_id: str | None, kind: str) -> list[dict[str, Any]]:
        normalized = []
        for row in rows:
            period = str(row.get("period", ""))
            month, week = self._period_keys(period, kind)
            pnl = float(row.get("pnl_krw", 0.0) or 0.0)
            normalized.append(
                {
                    **row,
                    "route_id": route_id,
                    "route_label": self._alias(route_id),
                    "kind": kind,
                    "month": month,
                    "week": week,
                    "result": "수익" if pnl > 0 else "손실" if pnl < 0 else "보합",
                    "trade_comment": self._trade_comment(int(row.get("trade_count", 0) or 0)),
                }
            )
        return normalized

    def _fill_daily_calendar(
        self,
        rows: list[dict[str, Any]],
        route_id: str | None,
        start_date: str,
        end_date: str | None,
        initial_cash_krw: float,
    ) -> list[dict[str, Any]]:
        if not end_date:
            return rows
        by_day = {str(row.get("period", ""))[:10]: row for row in rows if row.get("period")}
        try:
            cursor = date.fromisoformat(start_date[:10])
            end = date.fromisoformat(end_date[:10])
        except ValueError:
            return rows
        filled: list[dict[str, Any]] = []
        last_equity = initial_cash_krw
        while cursor <= end:
            period = cursor.isoformat()
            row = by_day.get(period)
            if row:
                last_equity = float(row.get("end_equity_krw", row.get("start_equity_krw", last_equity)) or last_equity)
                filled.append(row)
            else:
                month, week = self._period_keys(period, "daily")
                filled.append(
                    {
                        "period": period,
                        "trade_count": 0,
                        "start_equity_krw": last_equity,
                        "end_equity_krw": last_equity,
                        "pnl_krw": 0.0,
                        "return_pct": 0.0,
                        "mdd_pct": None,
                        "route_id": route_id,
                        "route_label": self._alias(route_id),
                        "kind": "daily",
                        "month": month,
                        "week": week,
                        "result": "거래없음",
                        "trade_comment": "주 시나리오 기준 체결 없음. 후보 미충족 또는 가드/필터 대기.",
                    }
                )
            cursor += timedelta(days=1)
        return filled

    def _trade_comment(self, trade_count: int) -> str:
        if trade_count > 0:
            return f"{trade_count}건 체결 기록 있음"
        return "체결 없음. 후보 미충족 또는 가드/필터 대기."

    def _period_keys(self, period: str, kind: str) -> tuple[str, str]:
        if kind == "monthly":
            return period[:7], ""
        if kind == "daily":
            try:
                parsed = date.fromisoformat(period[:10])
                return parsed.strftime("%Y-%m"), f"{parsed.isocalendar().year}-W{parsed.isocalendar().week:02d}"
            except ValueError:
                return period[:7], ""
        if kind == "weekly" and "-W" in period:
            try:
                year, week = period.split("-W", 1)
                parsed = date.fromisocalendar(int(year), int(week), 4)
                return parsed.strftime("%Y-%m"), period
            except ValueError:
                return period[:7], period
        return period[:7], period

    def _rank_monthly_routes(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            groups.setdefault(str(row.get("period", "")), []).append(row)
        ranked = []
        for period in sorted(groups):
            items = groups[period]
            best = max(items, key=lambda row: float(row.get("return_pct", -999.0)), default={})
            worst = min(items, key=lambda row: float(row.get("return_pct", 999.0)), default={})
            for row in sorted(items, key=lambda item: str(item.get("route_id", ""))):
                marker = ""
                if row is best:
                    marker = "best"
                elif row is worst:
                    marker = "worst"
                ranked.append({**row, "comparison_rank": marker})
        return ranked

    def _merge_routes(self, *route_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for row in [row for group in route_groups for row in group]:
            scenario = row.get("scenario")
            if not scenario:
                continue
            merged[scenario] = {**merged.get(scenario, {}), **row, "scenario_label": self._alias(scenario)}
        return list(merged.values())

    def _scenario_policy(self, routes: list[dict[str, Any]], active_route: str | None, backfill: dict[str, Any]) -> dict[str, Any]:
        ranked = sorted(routes, key=self._route_score, reverse=True)
        maintained = ranked[:5]
        research = ranked[5:]
        active = next((row for row in ranked if row.get("scenario") == active_route), {})
        if active_route and active and not any(row.get("scenario") == active_route for row in maintained):
            if len(maintained) >= 5:
                research = [maintained[-1], *research]
                maintained = [*maintained[:4], active]
            else:
                maintained = [*maintained, active]
        recommendation = self._route_agent_recommendation(maintained, active_route, backfill)
        recommended_route = recommendation.get("recommended_route")
        recommended_validated = next(
            (
                row
                for row in maintained
                if row.get("scenario") == recommended_route and self._has_period_records(backfill, row.get("scenario"))
            ),
            {},
        )
        best_validated = next((row for row in maintained if self._has_period_records(backfill, row.get("scenario"))), maintained[0] if maintained else {})
        primary = recommended_validated.get("scenario") or best_validated.get("scenario") or active_route
        if active_route and primary != active_route and active:
            active = {**active, "route_status": "SHADOW_PREVIOUS_PRIMARY"}
            maintained = [row if row.get("scenario") != active_route else active for row in maintained]
        return {
            "investment_start_date": "2026-01-01",
            "primary_route": primary,
            "primary_route_label": self._alias(primary),
            "previous_primary_route": active_route if primary != active_route else None,
            "previous_primary_route_label": self._alias(active_route) if primary != active_route else None,
            "max_maintained_routes": 5,
            "maintained_routes": maintained,
            "shadow_routes": [row for row in maintained if row.get("scenario") != primary],
            "research_routes": research,
            "daily_llm_feedback": {
                "status": "READY_NOT_SCHEDULED",
                "planned_report": "market-regime scenario feedback",
                "auto_apply_allowed": False,
            },
            "route_agent_recommendation": recommendation,
        }

    def _route_score(self, row: dict[str, Any]) -> tuple[float, float, float]:
        return (
            float(row.get("return_pct", -999.0) or -999.0),
            float(row.get("mdd_pct", -999.0) or -999.0),
            float(row.get("profit_factor", 0.0) or 0.0),
        )

    def _has_period_records(self, backfill: dict[str, Any], route_id: str | None) -> bool:
        return bool(route_id and backfill.get("monthly_returns", {}).get(route_id))

    def _alias(self, route_id: str | None) -> str:
        if not route_id:
            return "-"
        return ROUTE_ALIASES.get(route_id, str(route_id).replace("_", "-")[:18])

    def _record_staleness(self, latest_record_date: str | None) -> dict[str, Any]:
        if not latest_record_date:
            return {"status": "NO_RECORD", "days_behind": None, "message": "투자 기록 없음"}
        try:
            latest = datetime.fromisoformat(latest_record_date[:10]).date()
            today = date.today()
            days = (today - latest).days
        except ValueError:
            return {"status": "UNKNOWN", "days_behind": None, "message": "날짜 해석 실패"}
        if days <= 1:
            status = "FRESH"
            message = "최신 paper 기록 연결"
        else:
            status = "STALE"
            message = f"{latest_record_date} 이후 기록 갱신 필요"
        return {"status": status, "days_behind": days, "message": message}

    def _route_agent_recommendation(
        self,
        routes: list[dict[str, Any]],
        active_route: str | None,
        backfill: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        active = next((row for row in routes if row.get("scenario") == active_route), {})
        if not active:
            return {"recommended_route": active_route, "reason": "active route 기준 정보 없음", "auto_apply_allowed": False}
        eligible = []
        for row in routes:
            if row.get("scenario") == active_route:
                continue
            if backfill is not None and not self._has_period_records(backfill, row.get("scenario")):
                continue
            better_return = float(row.get("return_pct", -999.0)) > float(active.get("return_pct", -999.0))
            better_mdd = float(row.get("mdd_pct", -999.0)) >= float(active.get("mdd_pct", -999.0))
            if better_return and better_mdd:
                eligible.append(row)
        best = max(eligible, key=lambda row: (float(row.get("return_pct", -999.0)), float(row.get("mdd_pct", -999.0))), default={})
        if best:
            return {
                "recommended_route": best.get("scenario"),
                "reason": "active보다 수익률이 높고 MDD도 개선된 paper candidate",
                "return_delta_pct": float(best.get("return_pct", 0.0)) - float(active.get("return_pct", 0.0)),
                "mdd_delta_pct": float(best.get("mdd_pct", 0.0)) - float(active.get("mdd_pct", 0.0)),
                "auto_apply_allowed": False,
            }
        return {"recommended_route": active_route, "reason": "수익률과 MDD를 동시에 개선한 shadow 없음", "auto_apply_allowed": False}

    def _trade_logs(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        logs: list[dict[str, Any]] = []
        for row in rows:
            base = {
                "trade_id": row.get("trade_id"),
                "route_id": row.get("route_id"),
                "route_label": self._alias(row.get("route_id")),
                "route_status": row.get("route_status"),
                "market": row.get("market"),
                "source_mode": row.get("source_mode"),
                "real_order_enabled": row.get("real_order_enabled", False),
                "live_order_allowed": row.get("live_order_allowed", False),
                "auto_apply_allowed": row.get("auto_apply_allowed", False),
            }
            if row.get("entry_time"):
                logs.append(
                    {
                        **base,
                        "time": row.get("entry_time"),
                        "action": "매수",
                        "size_krw": row.get("size_krw"),
                        "realized_pnl_krw": None,
                        "pnl_pct": None,
                        "reason": "진입",
                    }
                )
            if row.get("exit_time"):
                logs.append(
                    {
                        **base,
                        "time": row.get("exit_time"),
                        "action": "매도/청산",
                        "size_krw": row.get("size_krw"),
                        "realized_pnl_krw": row.get("realized_pnl_krw", row.get("pnl_krw")),
                        "pnl_pct": row.get("pnl_pct"),
                        "reason": row.get("exit_reason"),
                    }
                )
        return sorted(logs, key=lambda item: str(item.get("time", "")), reverse=True)

    def _scenario_logs(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        logs = []
        for row in rows:
            logs.append(
                {
                    "time": row.get("decision_time"),
                    "market": row.get("market"),
                    "route_id": row.get("route_id"),
                    "route_label": self._alias(row.get("route_id")),
                    "route_status": row.get("route_status"),
                    "market_state": row.get("market_state"),
                    "selected_agent": row.get("selected_agent"),
                    "action": row.get("action"),
                    "size_krw": row.get("size_krw"),
                    "guard_on": row.get("guard_on"),
                    "hard_guard": row.get("hard_guard"),
                    "dominance_risk": row.get("dominance_risk"),
                    "pf20": row.get("pf20"),
                    "month_return_pct": row.get("month_return_pct"),
                    "hwm_drawdown_pct": row.get("hwm_drawdown_pct"),
                    "reason": row.get("reason"),
                    "real_order_enabled": row.get("real_order_enabled", False),
                    "live_order_allowed": row.get("live_order_allowed", False),
                    "auto_apply_allowed": row.get("auto_apply_allowed", False),
                }
            )
        return sorted(logs, key=lambda item: str(item.get("time", "")), reverse=True)
