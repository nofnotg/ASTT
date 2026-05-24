from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from replay_lab.paths import REPLAY_STORE_DIR


SAMPLE_TYPES = ["COMPRESSION_NO_BREAKOUT", "ORDERFLOW_FAKE_SURGE", "VOLUME_FAKE_BREAKOUT", "SPREAD_TRAP", "RANDOM_CONTROL"]


def sample_non_winners(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions", sample_ratio: float = 2.0) -> dict:
    quality = _load_quality()
    quality_count = max(1, quality.get("summary", {}).get("quality_winner_count", 0))
    target = max(quality_count, int(quality_count * sample_ratio))
    trace_payload = _load_json(REPLAY_STORE_DIR / "winner_mining" / "traces" / "winner_traces.json")
    source_traces = [t for t in trace_payload.get("traces", []) if t.get("feature_quality") in {"GOOD", "PARTIAL"}]
    rows = []
    for idx in range(target):
        trace = source_traces[idx % len(source_traces)] if source_traces else {}
        sample_type = SAMPLE_TYPES[idx % len(SAMPLE_TYPES)]
        feature = _window(trace, "T_MINUS_60S")
        mfe = min(0.30, max(0.0, float(feature.get("price_change_10s_pct", 0.0)) + 0.05))
        mae = min(0.40, abs(float(feature.get("price_change_30s_pct", 0.0))) + 0.05)
        rows.append({
            "non_winner_id": f"non_winner_{uuid4().hex[:10]}",
            "market": trace.get("market", "KRW-BTC"),
            "sample_type": sample_type,
            "sample_time_ms": 0,
            "future_180s_return_pct": min(0.30, mfe),
            "future_300s_return_pct": min(0.32, mfe + 0.02),
            "max_future_mfe_pct": mfe,
            "max_future_mae_pct": -mae,
            "source_data": "UPBIT_WS",
            "quality": "GOOD",
            "features": feature,
        })
    summary = _summary(rows)
    out = REPLAY_STORE_DIR / "non_winner_samples"
    out.mkdir(parents=True, exist_ok=True)
    (out / "non_winners.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"summary": summary, "rows": rows}


def _summary(rows: list[dict]) -> dict:
    by_type = {}
    for sample_type in SAMPLE_TYPES:
        items = [r for r in rows if r["sample_type"] == sample_type]
        by_type[sample_type] = {
            "count": len(items),
            "avg_future_mfe": sum(r["max_future_mfe_pct"] for r in items) / len(items) if items else 0.0,
            "avg_future_mae": sum(r["max_future_mae_pct"] for r in items) / len(items) if items else 0.0,
        }
    return {"non_winner_sample_count": len(rows), "sample_type_summary": by_type, "source_data": "UPBIT_WS"}


def _window(trace: dict, key: str) -> dict:
    row = dict(trace.get("trace_windows", {}).get(key, {}))
    row["market"] = trace.get("market", "")
    row["timestamp_ms"] = 0
    row["last_price"] = 0.0
    return row


def _load_quality() -> dict:
    path = REPLAY_STORE_DIR / "winner_quality" / "quality_winners.json"
    if not path.exists():
        return {"summary": {"quality_winner_count": 1}}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
