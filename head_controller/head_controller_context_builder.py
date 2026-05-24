from __future__ import annotations

import json
from pathlib import Path


def build_head_controller_context(reports_dir: str | Path = "docs/reports") -> dict:
    base = Path(reports_dir)
    return {
        "session_summary": _read(base / "latest_realistic_paper_summary.json"),
        "entry_discovery": _read(base / "latest_entry_discovery_summary.json"),
        "constraints": {"real_order_enabled": False, "live_readiness": "LIVE_NOT_ALLOWED", "auto_apply_config": False},
    }


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
