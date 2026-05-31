from __future__ import annotations

from local_dashboard.dashboard_data_service import DashboardDataService


def check_dashboard_health(reports_dir: str = "docs/reports") -> dict[str, object]:
    return DashboardDataService(reports_dir).health()
