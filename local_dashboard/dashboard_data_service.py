from __future__ import annotations

import json
from datetime import date
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
        return {
            "mode": backfill.get("mode", "PAPER_ONLY"),
            "source_mode": backfill.get("source_mode", "historical_backfill"),
            "start_date": backfill.get("start_date", "2026-01-01"),
            "initial_cash_krw": backfill.get("initial_cash_krw", 0.0),
            "active_route": active_route,
            "routes": backfill.get("routes", runtime.get("routes", [])),
            "monthly": monthly,
            "weekly": weekly,
            "daily": daily,
            "monthly_by_route": sorted(monthly_by_route, key=lambda row: (row.get("period", ""), row.get("route_id", ""))),
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
