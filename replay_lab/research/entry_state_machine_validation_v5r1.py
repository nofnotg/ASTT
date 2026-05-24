from __future__ import annotations

import json
from pathlib import Path

from timing_lab.timing_labeler import label_event_clips
from timing_lab.timing_state_machine import validate_state_machine_for_clips


def validate_entry_state_machine_v5r1(clips_dir: str | Path) -> dict:
    labels = label_event_clips(clips_dir).get("labels", [])
    summary = validate_state_machine_for_clips(clips_dir, labels)
    out = Path("replay_store/timing_state_replay")
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_state_machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
