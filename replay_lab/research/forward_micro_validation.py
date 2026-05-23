from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def validate_forward_micro_sessions(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "live_micro", min_quality: str = "PARTIAL", cost_scenarios=None) -> dict:
    summaries = _summaries(Path(sessions_dir))
    rows = []
    for item in summaries:
        rows.extend(item.get("paper_results", []))
    groups = {
        "ALL": rows,
        "GOOD_ONLY": rows if any("GOOD" in s.get("data_quality_summary", {}) for s in summaries) else [],
        "GOOD_PLUS_PARTIAL": rows if any(set(s.get("data_quality_summary", {})) & {"GOOD", "PARTIAL"} for s in summaries) else [],
        "POOR_OR_UNAVAILABLE": rows if any(set(s.get("data_quality_summary", {})) & {"POOR", "UNAVAILABLE"} for s in summaries) else [],
    }
    results = {name: _metrics(data) for name, data in groups.items()}
    return {"session_count": len(summaries), "good_session_count": sum(1 for s in summaries if "GOOD" in s.get("data_quality_summary", {})), "results": results, "live_readiness": _readiness(results)}


def _summaries(root: Path) -> list[dict]:
    if not root.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in root.glob("*/session_summary.json")]


def _metrics(rows: list[dict]) -> dict:
    pnl = [float(r.get("pnl_pct", 0.0)) for r in rows]
    realistic = [float(r.get("realistic_1_pnl_pct", 0.0)) for r in rows]
    wins = [x for x in realistic if x > 0]
    losses = [x for x in realistic if x < 0]
    gross_wins = [x for x in pnl if x > 0]
    gross_losses = [x for x in pnl if x < 0]
    return {"entry_count": len(rows), "cancel_count": 0, "win_rate": len(wins) / len(rows) if rows else 0.0, "profit_factor_gross": sum(gross_wins) / abs(sum(gross_losses)) if gross_losses else (999.0 if gross_wins else 0.0), "profit_factor_realistic_1": sum(wins) / abs(sum(losses)) if losses else (999.0 if wins else 0.0), "expectancy_realistic_1": sum(realistic) / len(realistic) if realistic else 0.0, "total_pnl_krw_realistic_1": sum(float(r.get("realistic_1_pnl_krw", 0.0)) for r in rows), "micro_cancel_effect": 0, "micro_exit_effect": 0}


def _readiness(results: dict) -> str:
    gp = results.get("GOOD_PLUS_PARTIAL", {})
    if gp.get("entry_count", 0) < 30 or gp.get("profit_factor_realistic_1", 0.0) < 1.1 or gp.get("expectancy_realistic_1", 0.0) <= 0:
        return "LIVE_NOT_ALLOWED"
    return "PAPER_MORE_REQUIRED"
