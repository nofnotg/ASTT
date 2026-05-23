from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


PRIORITY_MAP = {
    "VWAP_PULLBACK": "VWAP Pullback",
    "EMA_PULLBACK": "EMA Pullback",
    "ORDERBOOK_IMBALANCE": "Orderbook Imbalance",
}


def validate_priority_external_strategies_ws_v554(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "forward_ws_v554") -> dict:
    root = Path(sessions_dir)
    events = []
    for path in sorted(root.glob("*/candidate_events.json")):
        events.extend(json.loads(path.read_text(encoding="utf-8")))
    rows = []
    for key, label in PRIORITY_MAP.items():
        subset = [event for event in events if event.get("strategy_id") == key]
        blocks = Counter(event.get("primary_block_reason", "UNKNOWN_BLOCK") for event in subset)
        rows.append(
            {
                "strategy": label,
                "strategy_id": key,
                "candidate_count": len(subset),
                "enter_count": sum(1 for event in subset if event.get("entry_decision") == "ENTER"),
                "main_block_reason": blocks.most_common(1)[0][0] if blocks else "NO_DATA",
                "orderbook_available_ratio": sum(1 for event in subset if event.get("orderbook_available")) / len(subset) if subset else 0.0,
                "realistic_1_cost_survival": False,
                "block_reason_counts": dict(blocks),
            }
        )
    result = {"sessions_dir": str(root), "strategy_results": rows, "most_promising_strategy": _best(rows)}
    out = REPLAY_STORE_DIR / "reports" / "micro_entry_diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "priority_external_strategy_ws_v554.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def _best(rows: list[dict]) -> str:
    if not rows:
        return "NO_DATA"
    return sorted(rows, key=lambda row: (row["enter_count"], row["orderbook_available_ratio"], row["candidate_count"]), reverse=True)[0]["strategy"]
