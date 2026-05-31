from __future__ import annotations

from analysis.v686_runtime_dashboard import run_v686_control_tower_dashboard_review


def run_dashboard_review(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, object]:
    return run_v686_control_tower_dashboard_review(reports_dir, llm_provider)
