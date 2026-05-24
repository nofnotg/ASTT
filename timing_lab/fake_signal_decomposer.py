from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from timing_lab.event_clip_store import read_jsonl


SUBTYPES = [
    "VOLUME_ONLY_FAKE",
    "ORDERFLOW_ONLY_FAKE",
    "RANK_SURGE_FAKE",
    "SPREAD_ONLY_FAKE",
    "DEPTH_ONLY_FAKE",
    "BTC_NOISE_FAKE",
    "LATE_REACTION_FAKE",
    "NO_FOLLOW_THROUGH",
    "UNKNOWN",
]


def decompose_fake_signals(clips_dir: str | Path, labels_path: str | Path = "replay_store/timing_labels/latest_timing_labels.json") -> dict[str, Any]:
    labels = _read(labels_path).get("labels", [])
    rows = []
    for label in labels:
        if label.get("original_label") == "FAKE_SIGNAL" or label.get("label") == "FAKE_SIGNAL":
            meta, trades, orderbooks = _clip_data(Path(clips_dir), label["clip_id"])
            rows.append(_decompose(label, meta, trades, orderbooks))
    counts = Counter(row["fake_subtype"] for row in rows)
    event_counts = defaultdict(Counter)
    actions = {}
    for row in rows:
        event_counts[row["fake_subtype"]][row["event_type"]] += 1
        actions[row["fake_subtype"]] = row["suggested_action"]
    total = max(1, len(rows))
    summary = {
        "fake_signal_count": len(rows),
        "decomposed_count": sum(v for k, v in counts.items() if k != "UNKNOWN"),
        "unknown_count": counts.get("UNKNOWN", 0),
        "unknown_rate": counts.get("UNKNOWN", 0) / total,
        "subtype_counts": dict(counts),
        "subtype_table": [
            {
                "fake_subtype": subtype,
                "count": counts.get(subtype, 0),
                "pct": counts.get(subtype, 0) / total * 100,
                "main_event_type": event_counts[subtype].most_common(1)[0][0] if event_counts[subtype] else "",
                "suggested_action": actions.get(subtype, "KEEP_FOR_OBSERVATION"),
            }
            for subtype in SUBTYPES
        ],
        "rows": rows,
    }
    _write(Path("replay_store/fake_signal/fake_signal_decomposition.json"), summary)
    return summary


def _decompose(label: dict[str, Any], meta: dict[str, Any], trades: list[dict[str, Any]], orderbooks: list[dict[str, Any]]) -> dict[str, Any]:
    event_type = meta.get("event_type", _event_type_from_id(label.get("event_id", "")))
    subtype = {
        "VOLUME_SPIKE": "VOLUME_ONLY_FAKE",
        "ORDERFLOW_SHIFT": "ORDERFLOW_ONLY_FAKE",
        "MARKET_RANK_SURGE": "RANK_SURGE_FAKE",
        "SPREAD_CONTRACTION": "SPREAD_ONLY_FAKE",
        "DEPTH_RECOVERY": "DEPTH_ONLY_FAKE",
        "BTC_SHOCK": "BTC_NOISE_FAKE",
    }.get(event_type, "NO_FOLLOW_THROUGH")
    if label.get("max_mfe_pct", 0) > 0.08 and label.get("max_effective_return_pct", 0) <= 0:
        subtype = "LATE_REACTION_FAKE"
    evidence = {"trade_count": len(trades), "orderbook_count": len(orderbooks), "max_mfe_pct": label.get("max_mfe_pct", 0.0)}
    action = "PAUSE_EVENT_TYPE" if subtype in {"RANK_SURGE_FAKE", "SPREAD_ONLY_FAKE", "DEPTH_ONLY_FAKE", "BTC_NOISE_FAKE"} else "TIGHTEN_FILTER"
    if subtype == "NO_FOLLOW_THROUGH":
        action = "KEEP_FOR_OBSERVATION"
    return {
        "clip_id": label["clip_id"],
        "event_id": label.get("event_id", ""),
        "market": label.get("market", ""),
        "event_type": event_type,
        "original_label": "FAKE_SIGNAL",
        "fake_subtype": subtype,
        "evidence": evidence,
        "dominant_reason": subtype,
        "secondary_reasons": list(label.get("reason", [])),
        "suggested_action": action,
    }


def _clip_data(root: Path, clip_id: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    for meta_path in root.glob(f"*\\{clip_id}\\clip_meta.json"):
        meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        return meta, read_jsonl(meta_path.parent / "trades.jsonl"), read_jsonl(meta_path.parent / "orderbooks.jsonl")
    return {}, [], []


def _event_type_from_id(event_id: str) -> str:
    for name in ["VOLUME_SPIKE", "ORDERFLOW_SHIFT", "SPREAD_CONTRACTION", "DEPTH_RECOVERY", "RANGE_TOUCH", "BREAKOUT_PRESSURE", "BTC_SHOCK", "MARKET_RANK_SURGE"]:
        if name in event_id:
            return name
    return "UNKNOWN"


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
