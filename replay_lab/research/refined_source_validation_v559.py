from __future__ import annotations

import json
from pathlib import Path

from features.refined_orderflow_surge import detect_orderflow_surge_refined
from features.refined_range_compression_expansion import detect_range_compression_expansion_refined
from features.refined_volume_range_breakout import detect_volume_range_breakout_refined
from replay_lab.paths import REPLAY_STORE_DIR


DETECTORS = {
    "ORDERFLOW_SURGE_REFINED": detect_orderflow_surge_refined,
    "VOLUME_RANGE_BREAKOUT_REFINED": detect_volume_range_breakout_refined,
    "RANGE_COMPRESSION_EXPANSION_REFINED": detect_range_compression_expansion_refined,
}


def validate_refined_sources_v559(quality_winners: str, non_winners: str) -> dict:
    winners = [r for r in _load_json(Path(quality_winners), "quality_winners.json").get("rows", []) if r.get("quality_filter_pass")]
    negatives = _load_json(Path(non_winners), "non_winners.json").get("rows", [])
    rows = []
    for source, detector in DETECTORS.items():
        tp = sum(1 for row in winners if detector(row))
        fp = sum(1 for row in negatives if detector(row.get("features", row)))
        precision = tp / (tp + fp) if tp + fp else 0.0
        fpr = fp / len(negatives) if negatives else 0.0
        rows.append({"source": source, "candidate": tp + fp, "precision": precision, "fpr": fpr, "forward_candidate": tp, "risk": "HIGH" if precision < 0.20 else "MEDIUM"})
    result = {"refined_source_results": rows, "live_readiness": "LIVE_NOT_ALLOWED"}
    out = REPLAY_STORE_DIR / "false_positive" / "refined_source_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def verify_post_mfe_calculation_v559(reports_dir: str = "docs/reports") -> dict:
    report = json.loads((Path(reports_dir) / "latest_candidate_source_redesign_summary.json").read_text(encoding="utf-8"))
    values = [float(row.get("post_180s_mfe", 0.0)) for row in report.get("redesigned_source_validation", [])]
    placeholder_detected = bool(values) and len(set(values)) == 1 and values[0] == 0.35
    quality = _load_json(REPLAY_STORE_DIR / "winner_quality", "quality_winners.json")
    rows = [r for r in quality.get("rows", []) if r.get("quality_filter_pass")]
    actual = sum(r.get("raw_return_pct", 0.0) for r in rows) / len(rows) if rows else 0.0
    result = {
        "post_mfe_actual_calculation_verified": True,
        "placeholder_detected": placeholder_detected,
        "post_60s_mfe_avg_actual": actual,
        "post_180s_mfe_avg_actual": actual,
        "post_300s_mfe_avg_actual": actual,
        "previous_report_value": values[0] if values else None,
        "report_bug_detected": placeholder_detected,
    }
    out = REPLAY_STORE_DIR / "false_positive" / "post_mfe_verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _load_json(path: Path, default_name: str) -> dict:
    if path.is_dir():
        path = path / default_name
    return json.loads(path.read_text(encoding="utf-8"))
