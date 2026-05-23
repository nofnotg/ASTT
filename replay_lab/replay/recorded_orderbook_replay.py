from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def load_recorded_orderbooks(session_id: str, root: Path = REPLAY_STORE_DIR) -> list[dict]:
    rows = []
    for path in (root / "raw" / "live_micro").glob("*/orderbooks/*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("session_id") == session_id:
                rows.append(row)
    return sorted(rows, key=lambda r: r.get("timestamp_ms", 0))
