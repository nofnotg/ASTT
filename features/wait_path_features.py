from __future__ import annotations

HORIZONS = (10, 30, 60, 180, 300)


def compute_wait_path_features(candidate: dict, snapshots: list[dict], horizons: tuple[int, ...] = HORIZONS) -> dict:
    entry = float(candidate.get("reference_price") or 0)
    start = int(candidate.get("candidate_time_ms") or 0)
    future = [s for s in snapshots if s.get("market") == candidate.get("market") and int(s.get("timestamp_ms", 0)) >= start]
    result = {
        "candidate_id": candidate.get("candidate_id", ""),
        "market": candidate.get("market", ""),
        "candidate_source": candidate.get("candidate_source", ""),
        "decision": "WAIT",
        "research_only": True,
        "included_in_pnl": False,
    }
    if not entry or not future:
        result.update({"best_mfe_pct": 0.0, "worst_mae_pct": 0.0, "time_to_best_mfe_seconds": None, "time_to_worst_mae_seconds": None, "wait_classification": "INCONCLUSIVE"})
        return _with_horizon_defaults(result, horizons)

    best = (-10**9, None)
    worst = (10**9, None)
    for horizon in horizons:
        scoped = [s for s in future if int(s.get("timestamp_ms", 0)) <= start + horizon * 1000]
        mfe, mae = _mfe_mae(entry, scoped)
        result[f"post_{horizon}s_mfe_pct"] = mfe
        result[f"post_{horizon}s_mae_pct"] = mae
    for snap in future:
        sec = int((int(snap.get("timestamp_ms", 0)) - start) / 1000)
        pct = (float(snap.get("last_price") or entry) - entry) / entry * 100
        if pct > best[0]:
            best = (pct, sec)
        if pct < worst[0]:
            worst = (pct, sec)
    result.update({
        "best_mfe_pct": best[0],
        "worst_mae_pct": worst[0],
        "time_to_best_mfe_seconds": best[1],
        "time_to_worst_mae_seconds": worst[1],
        "would_hit_target_0_35": best[0] >= 0.35,
        "would_hit_target_0_50": best[0] >= 0.50,
        "would_hit_target_0_80": best[0] >= 0.80,
        "would_hit_stop_0_25": worst[0] <= -0.25,
        "would_hit_stop_0_35": worst[0] <= -0.35,
    })
    result["wait_classification"] = classify_wait_path(result, candidate)
    return result


def classify_wait_path(row: dict, candidate: dict | None = None) -> str:
    if row.get("post_60s_mfe_pct", 0) >= 0.35 and row.get("post_60s_mae_pct", 0) >= -0.25:
        return "MISSED_WIN"
    if row.get("best_mfe_pct", 0) < 0.20 or row.get("worst_mae_pct", 0) <= -0.35:
        return "CORRECTLY_BLOCKED"
    if candidate and float(candidate.get("evidence", {}).get("pre_move_pct", 0) or 0) >= 0.5 and row.get("best_mfe_pct", 0) < 0.25:
        return "LATE_SIGNAL"
    if (row.get("time_to_best_mfe_seconds") or 0) >= 180 and row.get("best_mfe_pct", 0) >= 0.35:
        return "TOO_EARLY_SIGNAL"
    return "INCONCLUSIVE"


def _mfe_mae(entry: float, snapshots: list[dict]) -> tuple[float, float]:
    if not snapshots:
        return 0.0, 0.0
    moves = [(float(s.get("last_price") or entry) - entry) / entry * 100 for s in snapshots]
    return max(moves), min(moves)


def _with_horizon_defaults(row: dict, horizons: tuple[int, ...]) -> dict:
    for horizon in horizons:
        row[f"post_{horizon}s_mfe_pct"] = 0.0
        row[f"post_{horizon}s_mae_pct"] = 0.0
    row.update({"would_hit_target_0_35": False, "would_hit_target_0_50": False, "would_hit_target_0_80": False, "would_hit_stop_0_25": False, "would_hit_stop_0_35": False})
    return row
