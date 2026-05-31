from __future__ import annotations

from local_dashboard.dashboard_data_service import DashboardDataService


def test_v686_dashboard_api_returns_health_and_routes(tmp_path) -> None:
    reports = tmp_path
    (reports / "latest_v686_active_shadow_runtime_summary.json").write_text('{"active_route":"LG_V2_BALANCED_PLUS_DOM_GATE","routes":[]}', encoding="utf-8")
    service = DashboardDataService(str(reports))
    assert service.health()["dashboard_ready"] is True
    assert service.routes()["active_route"] == "LG_V2_BALANCED_PLUS_DOM_GATE"
