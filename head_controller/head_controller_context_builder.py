from __future__ import annotations

import json
from pathlib import Path


def build_head_controller_context(reports_dir: str | Path = "docs/reports", llm_config: dict | None = None) -> dict:
    base = Path(reports_dir)
    return {
        "session_summary": _read(base / "latest_realistic_paper_summary.json"),
        "entry_discovery": _read(base / "latest_entry_discovery_summary.json"),
        "llm_config": llm_config or {"llm_enabled": False, "selected_provider": "off", "auto_apply_allowed": False},
        "constraints": {"real_order_enabled": False, "live_readiness": "LIVE_NOT_ALLOWED", "auto_apply_config": False},
    }


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
