from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def write_config_patch(base_config_version: str, target_config_version: str, patch: dict, reason: str, created_by: str = "Athena") -> Path:
    patch_id = datetime.utcnow().strftime("patch_%Y%m%d_%H%M%S")
    data = {
        "patch_id": patch_id,
        "base_config_version": base_config_version,
        "target_config_version": target_config_version,
        "status": "DRAFT",
        "created_by": created_by,
        "reason": reason,
        "patch": patch,
        "expected_effect": "",
        "side_effect": "",
        "required_validation": ["90d_replay", "walk_forward", "shadow_mode"],
    }
    path = REPLAY_STORE_DIR / "exports" / "candidates" / f"{patch_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

