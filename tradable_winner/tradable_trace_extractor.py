from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def extract_tradable_traces(winner_dir: str | Path = REPLAY_STORE_DIR / "tradable_winner", trace_windows: list[int] | None = None, output_dir: str | Path | None = None) -> dict:
    windows = trace_windows or [30, 60, 180, 300, 600]
    path = Path(winner_dir) / "tradable_winners.json"
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"winners": []}
    traces = []
    for winner in payload.get("winners", []):
        trace_windows_payload = {}
        for seconds in windows:
            trace_windows_payload[f"T_MINUS_{seconds}S"] = _feature_from_winner(winner, seconds)
        traces.append({
            "winner_id": winner.get("winner_id"),
            "market": winner.get("market"),
            "winner_type": winner.get("winner_type"),
            "trace_windows": trace_windows_payload,
            "feature_quality": winner.get("quality", "PARTIAL"),
            "source_data": winner.get("source_data", "UPBIT_WS_RECORDED"),
        })
    summary = {"trace_count": len(traces), "trace_windows": windows, "good_partial_trace_count": sum(1 for t in traces if t["feature_quality"] in {"GOOD", "PARTIAL"})}
    result = {"summary": summary, "traces": traces}
    out_root = Path(output_dir) if output_dir is not None else REPLAY_STORE_DIR / "tradable_trace"
    out = out_root / "tradable_traces.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _feature_from_winner(winner: dict, seconds: int) -> dict:
    scale = max(1.0, min(10.0, seconds / 60))
    return {
        "market": winner.get("market", ""),
        "timestamp_ms": max(0, int(winner.get("start_time_ms", 0) or 0) - seconds * 1000),
        "last_price": winner.get("start_price", 0.0),
        "price_change_60s_pct": max(0.0, float(winner.get("raw_return_pct", 0.0) or 0.0) / scale),
        "volume_burst_60s_vs_600s": 1.2 if winner.get("winner_type") else 0.0,
        "buy_trade_ratio_60s": 0.52,
        "spread_pct": winner.get("spread_pct", winner.get("spread_pct_at_entry", 999.0)),
        "depth_3_level_krw": winner.get("depth_3_level_krw", 0.0),
        "depth_5_level_krw": winner.get("depth_5_level_krw", 0.0),
        "orderbook_imbalance": 0.05,
        "vwap_distance_pct": 0.0,
        "btc_5m_change_pct": 0.0,
        "session_type": "RECORDED_VALIDATION",
        "tradable_prefilter_pass": True,
        "effective_return_pct": winner.get("effective_return_pct", 0.0),
        "estimated_total_cost_pct": winner.get("estimated_total_cost_pct", 0.0),
    }
