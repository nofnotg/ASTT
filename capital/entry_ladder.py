from __future__ import annotations


def build_entry_ladder(allocation_krw: float) -> dict:
    parts = [(1, 0.3, "READY"), (2, 0.3, "WAIT_CONFIRM"), (3, 0.4, "WAIT_CONFIRM")]
    return {
        "ladder_plan": [
            {"step": step, "pct": pct, "krw": round(float(allocation_krw) * pct, 4), "status": status}
            for step, pct, status in parts
        ]
    }
