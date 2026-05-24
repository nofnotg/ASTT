from __future__ import annotations

ENTRY_DISCOVERY_PROFILES = {
    "STRICT": {"research_only": False, "min_best_mfe_pct": 0.35, "max_mae_pct": -0.25},
    "BALANCED": {"research_only": False, "min_best_mfe_pct": 0.30, "max_mae_pct": -0.30},
    "ENTRY_DISCOVERY": {"research_only": True, "min_best_mfe_pct": 0.20, "max_mae_pct": -0.40},
    "DIAGNOSTIC_ONLY": {"research_only": True, "diagnostic_only": True},
}


def get_entry_discovery_profile(name: str) -> dict:
    return ENTRY_DISCOVERY_PROFILES[name].copy()
