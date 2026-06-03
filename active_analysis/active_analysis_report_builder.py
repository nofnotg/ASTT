from __future__ import annotations

from pathlib import Path

from scenario_telemetry.v688_common import write_html


def build_active_analysis_report(payload: dict, reports_dir: str | Path = "docs/reports") -> str:
    return write_html(
        Path(reports_dir) / "latest_v688_active_analysis_recommendations_report.html",
        "V6.8.8 Active Analysis Recommendations",
        [("Recommendations", payload.get("recommendations", [])), ("Route State", payload.get("route_state", {})), ("Pipeline Health", payload.get("pipeline_health", {}))],
    )
