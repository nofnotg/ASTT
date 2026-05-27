from __future__ import annotations

from typing import Any


def audit_v672_btcdom_index_quality(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": summary.get("source_type"),
        "is_percentage": summary.get("is_percentage"),
        "quality": summary.get("data_quality"),
        "fake_data_generated": bool(summary.get("fake_data_generated")),
    }
