from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def audit_mock_vs_real_data(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions") -> dict:
    root = Path(sessions_dir)
    mock = 0
    real = 0
    eligible = 0
    mixed = False
    warnings = []
    for path in root.glob("*/*/session_summary.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        source = data.get("data_source") or ("MOCK" if "live_micro" in path.parts else "UNKNOWN")
        if source == "MOCK":
            mock += 1
            if data.get("eligible_for_live_readiness", False):
                mixed = True
                warnings.append(f"mock_eligible:{path}")
        elif source == "UPBIT_WS":
            real += 1
            if data.get("eligible_for_live_readiness"):
                eligible += 1
    return {"mock_session_count": mock, "real_session_count": real, "mixed_data_detected": mixed, "readiness_eligible_session_count": eligible, "mock_excluded_from_readiness": not mixed, "warnings": warnings}
