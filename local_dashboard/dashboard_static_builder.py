from __future__ import annotations

from pathlib import Path


def ensure_dashboard_static(root: str | Path = "local_dashboard") -> None:
    base = Path(root)
    (base / "templates").mkdir(parents=True, exist_ok=True)
    (base / "static").mkdir(parents=True, exist_ok=True)
