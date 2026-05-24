from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


FEATURES = [
    ("buy_trade_ratio_10s", "higher_is_better"),
    ("orderbook_imbalance", "higher_is_better"),
    ("spread_pct", "lower_is_better"),
    ("volume_burst_ratio_10s_vs_60s", "higher_is_better"),
    ("previous_high_distance_pct", "lower_is_better"),
]


def analyze_source_discriminative_power(quality_winners: str | Path = REPLAY_STORE_DIR / "winner_quality", non_winners: str | Path = REPLAY_STORE_DIR / "non_winner_samples") -> dict:
    winners = [r for r in _load_json(Path(quality_winners), "quality_winners.json").get("rows", []) if r.get("quality_filter_pass")]
    negatives = _load_json(Path(non_winners), "non_winners.json").get("rows", [])
    rows = []
    for feature, direction in FEATURES:
        w_avg = _avg(winners, feature)
        n_avg = _avg([r.get("features", r) for r in negatives], feature)
        denom = max(abs(w_avg), abs(n_avg), 1.0)
        score = abs(w_avg - n_avg) / denom
        rows.append({"feature": feature, "winner_avg": w_avg, "non_winner_avg": n_avg, "separation_score": score, "direction": direction})
    summary = {"feature_rows": rows, "top_features": [r["feature"] for r in sorted(rows, key=lambda x: x["separation_score"], reverse=True)[:3]]}
    out = REPLAY_STORE_DIR / "false_positive"
    out.mkdir(parents=True, exist_ok=True)
    (out / "source_discriminative_power.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _avg(rows: list[dict], feature: str) -> float:
    values = [float(r.get(feature, 0.0)) for r in rows if r.get(feature) is not None and float(r.get(feature, 0.0)) < 900]
    return sum(values) / len(values) if values else 0.0


def _load_json(path: Path, default_name: str) -> dict:
    if path.is_dir():
        path = path / default_name
    return json.loads(path.read_text(encoding="utf-8"))
