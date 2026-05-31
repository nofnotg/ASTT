from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardConfig:
    host: str = "127.0.0.1"
    port: int = 8787
    reports_dir: str = "docs/reports"
    data_dir: str = "data/paper"
