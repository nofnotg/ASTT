from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from local_dashboard.dashboard_security import security_status
from paper_runtime.paper_runtime_schema import safety_flags


class DashboardDataService:
    def __init__(self, reports_dir: str = "docs/reports", data_dir: str = "data/paper") -> None:
        self.reports = Path(reports_dir)
        self.data = Path(data_dir)

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
        runtime = self._read("latest_v686_active_shadow_runtime_summary.json")
        active_route = backfill.get("active_route") or runtime.get("active_route")
        daily = self._period_rows(backfill.get("daily_equity", {}).get(active_route, []), active_route, "daily")
        weekly = self._period_rows(backfill.get("weekly_returns", {}).get(active_route, []), active_route, "weekly")
        monthly = self._period_rows(backfill.get("monthly_returns", {}).get(active_route, []), active_route, "monthly")
        monthly_by_route: list[dict[str, Any]] = []
        for route_id, rows in backfill.get("monthly_returns", {}).items():
            monthly_by_route.extend(self._period_rows(rows, route_id, "monthly"))
        latest_record_date = max((str(row.get("period", "")) for row in daily), default=None)
        return {
            "mode": backfill.get("mode", "PAPER_ONLY"),
            "source_mode": backfill.get("source_mode", "historical_backfill"),
            "start_date": backfill.get("start_date", "2026-01-01"),
            "initial_cash_krw": backfill.get("initial_cash_krw", 0.0),
            "active_route": active_route,
            "routes": backfill.get("routes", runtime.get("routes", [])),
            "route_agent_recommendation": self._route_agent_recommendation(backfill.get("routes", runtime.get("routes", [])), active_route),
            "monthly": monthly,
            "weekly": weekly,
            "daily": daily,
            "monthly_by_route": self._rank_monthly_routes(monthly_by_route),
            "latest_record_date": latest_record_date,
            "record_staleness": self._record_staleness(latest_record_date),
            "latest_market_data": self._latest_market_data(),
            "latest_forward_ws": self._latest_forward_ws(),
            **safety_flags(),
        }

    def investment_logs(self, limit: int = 2000) -> dict[str, Any]:
        trades = self._read_jsonl(self.data / "journal" / "paper_trades.jsonl", limit)
        decisions = self._read_jsonl(self.data / "journal" / "paper_decisions.jsonl", limit)
        return {
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

    def pattern_validation(self) -> dict[str, Any]:
        return self._read("latest_v687_investment_pattern_validation_summary.json")

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
        root = Path("replay_store") / "sessions" / "forward_ws_v554"
        marker = root / "live_forward_process.json"
        files = sorted(root.glob("*/session_summary.json"), key=lambda path: path.stat().st_mtime, reverse=True)
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
        if not files:
            return running or {"status": "NO_FORWARD_WS_SESSION"}
        row = json.loads(files[0].read_text(encoding="utf-8-sig"))
        latest = {
            "session_id": row.get("session_id"),
            "status": row.get("status"),
            "duration_minutes": row.get("duration_minutes"),
            "trade_event_count": row.get("trade_event_count"),
            "orderbook_event_count": row.get("orderbook_event_count"),
            "candidate_count": row.get("candidate_count"),
            "enter_count": row.get("enter_count"),
            "wait_count": row.get("wait_count"),
            "real_order_enabled": row.get("real_order_enabled", False),
        }
        if running.get("status") == "RUNNING":
            return {**latest, **running, "last_completed_session_id": latest.get("session_id"), "last_completed_candidate_count": latest.get("candidate_count")}
        return latest

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
                    "kind": kind,
                    "month": month,
                    "week": week,
                    "result": "수익" if pnl > 0 else "손실" if pnl < 0 else "보합",
                }
            )
        return normalized

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

    def _route_agent_recommendation(self, routes: list[dict[str, Any]], active_route: str | None) -> dict[str, Any]:
        active = next((row for row in routes if row.get("scenario") == active_route), {})
        if not active:
            return {"recommended_route": active_route, "reason": "active route 기준 정보 없음", "auto_apply_allowed": False}
        eligible = []
        for row in routes:
            if row.get("scenario") == active_route:
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
