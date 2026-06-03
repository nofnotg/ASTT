from __future__ import annotations

from typing import Callable

from local_dashboard.dashboard_data_service import DashboardDataService


def route_map(service: DashboardDataService) -> dict[str, Callable[[], dict]]:
    return {
        "/api/health": service.health,
        "/api/account": service.account,
        "/api/routes": service.routes,
        "/api/positions": service.positions,
        "/api/trades": service.trades,
        "/api/decisions": service.decisions,
        "/api/investment-records": service.investment_records,
        "/api/investment-logs": service.investment_logs,
        "/api/active-shadow": service.active_shadow,
        "/api/bear-windows": service.bear_windows,
        "/api/atr-research": service.atr_research,
        "/api/pattern-validation": service.pattern_validation,
        "/api/control-tower": service.control_tower,
        "/api/v688-dashboard": service.v688_dashboard,
        "/api/v690-dashboard": service.v690_dashboard,
        "/api/v691-dashboard": service.v691_dashboard,
        "/api/v692-dashboard": service.v692_dashboard,
        "/api/v693-dashboard": service.v693_dashboard,
    }
