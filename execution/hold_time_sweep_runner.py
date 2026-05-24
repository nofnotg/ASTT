from __future__ import annotations

from features.hold_time_sweep_config import DEFAULT_HOLD_SECONDS


def run_hold_time_sweep(wait_path_result: dict, hold_seconds: list[int] | tuple[int, ...] = DEFAULT_HOLD_SECONDS) -> dict:
    rows = []
    wait_rows = wait_path_result.get("rows", [])
    for hold in hold_seconds:
        mfe_key = f"post_{hold}s_mfe_pct" if hold <= 300 else "best_mfe_pct"
        mae_key = f"post_{hold}s_mae_pct" if hold <= 300 else "worst_mae_pct"
        mfes = [float(row.get(mfe_key, 0) or 0) for row in wait_rows]
        maes = [float(row.get(mae_key, 0) or 0) for row in wait_rows]
        rows.append({
            "hold_seconds": hold,
            "candidate": len(wait_rows),
            "enter": 0,
            "research_wait": len(wait_rows),
            "mfe_avg": _avg(mfes),
            "mae_avg": _avg(maes),
            "target_hit_rate": sum(1 for value in mfes if value >= 0.35) / len(mfes) if mfes else 0.0,
            "stop_hit_rate": sum(1 for value in maes if value <= -0.25) / len(maes) if maes else 0.0,
            "research_only": True,
        })
    return {"rows": rows, "research_only": True, "included_in_live_readiness": False}


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
