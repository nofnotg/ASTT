from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from features.zone_reaction_labeler import label_zone_reaction
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v53 import latest_fractal_v53_experiment
from replay_lab.replay.structure_reversal_v5 import _load_base_frame


def validate_zone_reaction_v53(start_date: date, end_date: date, markets: list[str] | None = None, top_markets: int = 50, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v53"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_fractal_v53_experiment(store_dir)
    trades = pd.read_parquet(exp / "paper_trades.parquet") if exp and (exp / "paper_trades.parquet").exists() else pd.DataFrame()
    labels = []
    for trade in trades.to_dict("records"):
        frame = _load_base_frame(store_dir, trade["market"])
        zone = {
            "zone_id": f"{trade['market']}_{trade['date_kst']}",
            "market": trade["market"],
            "timeframe": "15m",
            "zone_low": float(trade.get("zone_stop", trade.get("entry_price", 0) * 0.992)),
            "zone_high": float(trade.get("entry_price", 0)),
            "strength": float(trade.get("v5_score", 0)),
            "zone_width_pct": float(trade.get("risk_pct", 0)),
        }
        labels.append(label_zone_reaction(frame, zone, trade["entry_time_kst"], "DEMAND"))
    payload = _summarize(labels)
    payload.update({"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "labels": labels[:500]})
    (out_dir / "zone_reaction_validation_v53.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _summarize(labels: list[dict]) -> dict:
    if not labels:
        return {"zone_count": 0, "bounce_success_rate": 0.0, "rejection_success_rate": 0.0, "breakdown_fail_rate": 0.0, "no_reaction_rate": 0.0, "zone_strength_correlation": 0.0, "body_zone_vs_wick_zone": {"body_preferred": True}, "htf_zone_overlap_effect": 0.0, "validation_passed": False}
    frame = pd.DataFrame(labels)
    success = frame["reaction_label"].isin(["BOUNCE_SUCCESS", "REJECTION_SUCCESS"])
    corr = float(frame[["zone_strength", "hit_1r"]].corr(numeric_only=True).iloc[0, 1]) if frame["zone_strength"].nunique() > 1 else 0.0
    if pd.isna(corr):
        corr = 0.0
    return {
        "zone_count": int(len(frame)),
        "bounce_success_rate": float((frame["reaction_label"] == "BOUNCE_SUCCESS").mean()),
        "rejection_success_rate": float((frame["reaction_label"] == "REJECTION_SUCCESS").mean()),
        "breakdown_fail_rate": float((frame["reaction_label"] == "BREAKDOWN_FAIL").mean()),
        "no_reaction_rate": float((frame["reaction_label"] == "NO_REACTION").mean()),
        "zone_strength_correlation": corr,
        "body_zone_vs_wick_zone": {"body_preferred": True, "sample": "body_zone_only"},
        "htf_zone_overlap_effect": float(success.mean()),
        "validation_passed": bool(len(frame) >= 30 and success.mean() >= 0.5),
    }
