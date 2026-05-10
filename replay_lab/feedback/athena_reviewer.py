from __future__ import annotations

import json
from pathlib import Path

from replay_lab.settings import ReplaySettings


def review_experiment(exp_dir: Path, settings: ReplaySettings | None = None) -> dict:
    settings = settings or ReplaySettings()
    metrics_path = exp_dir / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    entries = int(metrics.get("entries", 0))
    enough = entries >= settings.athena_min_sample_size
    recommendation = "HOLD"
    patches = []
    if enough and metrics.get("win_rate", 0) < 0.45:
        recommendation = "APPLY_TO_BACKTEST"
        patches.append({"field": "MIN_REZO_SCORE", "from": 80, "to": 85, "reason": "low replay win rate"})
    return {
        "summary": "Rule-based Athena review completed.",
        "sample_quality": {
            "trade_count": entries,
            "candidate_count": int(metrics.get("decisions", 0)),
            "enough_sample": enough,
            "warning": "" if enough else "sample size below threshold",
        },
        "module_diagnosis": {"Mr.K": "", "매기": "", "Rezo": "", "CostA": "", "Iris": ""},
        "failure_patterns": [],
        "missed_opportunities": [],
        "proposed_patches": patches,
        "overfitting_risk": "MEDIUM" if enough else "HIGH",
        "final_recommendation": recommendation if enough else "HOLD",
    }

