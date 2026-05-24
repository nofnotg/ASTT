from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def store_llm_proposal(proposal: dict, provider: str, artifact_integrity_status: str, created_by: str = "HEAD_CONTROLLER_LLM") -> Path:
    out = REPLAY_STORE_DIR / "head_controller" / "proposals"
    out.mkdir(parents=True, exist_ok=True)
    proposal_id = proposal.get("proposal_id") or f"proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    record = {
        "proposal_id": proposal_id,
        "created_at": datetime.now().isoformat(),
        "created_by": created_by,
        "source_reports": [],
        "artifact_integrity_status": artifact_integrity_status,
        "llm_provider": provider,
        "proposal": proposal,
        "active": False,
        "human_approved": False,
        "applied": False,
    }
    path = out / f"{proposal_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path
