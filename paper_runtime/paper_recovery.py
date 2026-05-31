from __future__ import annotations


def recovery_plan() -> dict[str, str]:
    return {"mode": "append_only_replay", "status": "READY"}
