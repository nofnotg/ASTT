from __future__ import annotations

from collections import Counter

from features.entry_discovery_profiles import ENTRY_DISCOVERY_PROFILES, get_entry_discovery_profile


def simulate_entry_discovery(wait_path_result: dict, profiles: list[str] | tuple[str, ...] = tuple(ENTRY_DISCOVERY_PROFILES)) -> dict:
    rows = []
    wait_rows = wait_path_result.get("rows", [])
    for name in profiles:
        profile = get_entry_discovery_profile(name)
        if profile.get("diagnostic_only"):
            enter = 0
            main = _main_class(wait_rows)
        else:
            enter = sum(1 for row in wait_rows if row.get("best_mfe_pct", 0) >= profile["min_best_mfe_pct"] and row.get("worst_mae_pct", 0) >= profile["max_mae_pct"])
            main = "TARGET_TOO_SMALL" if enter == 0 else "DISCOVERY_GATE_PASS"
        rows.append({"profile": name, "candidate": len(wait_rows), "enter": enter, "wait": len(wait_rows) - enter, "cancel": 0, "research_only": bool(profile.get("research_only")), "main_block_reason": main})
    return {"profiles": rows, "live_readiness": "LIVE_NOT_ALLOWED"}


def _main_class(rows: list[dict]) -> str:
    if not rows:
        return "NO_DATA"
    return Counter(row.get("wait_classification", "INCONCLUSIVE") for row in rows).most_common(1)[0][0]
