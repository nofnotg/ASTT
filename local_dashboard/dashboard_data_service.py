from __future__ import annotations

import json
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
