from __future__ import annotations

from pathlib import Path
from typing import Any

import json


def load_btcdom_index_quality(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v672_btcdom_index_data_quality_summary.json"
    if not path.exists():
        return {"data_quality": "UNAVAILABLE", "fake_data_generated": False}
    return json.loads(path.read_text(encoding="utf-8-sig"))
