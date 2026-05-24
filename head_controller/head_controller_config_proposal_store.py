from __future__ import annotations

import json
from datetime import datetime

from replay_lab.paths import REPLAY_STORE_DIR


def store_head_controller_config_proposal(proposal: dict) -> str:
    out = REPLAY_STORE_DIR / "head_controller" / "config_proposals"
    out.mkdir(parents=True, exist_ok=True)
    proposal_id = proposal.get("proposal_id") or datetime.now().strftime("config_proposal_%Y%m%d_%H%M%S")
    record = {**proposal, "proposal_id": proposal_id, "active": False, "human_approved": False, "applied": False}
    path = out / f"{proposal_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return str(path)
