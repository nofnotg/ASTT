from __future__ import annotations

import json
from pathlib import Path

from features.live_micro_quality import evaluate_live_micro_quality
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.recorded_orderbook_replay import load_recorded_orderbooks
from replay_lab.replay.recorded_trade_replay import load_recorded_trades


def replay_recorded_micro_session(session_id: str, config_path=None, output_dir: str | Path = "replay_store/replayed/live_micro", root: Path = REPLAY_STORE_DIR) -> dict:
    trades = load_recorded_trades(session_id, root)
    orderbooks = load_recorded_orderbooks(session_id, root)
    quality = evaluate_live_micro_quality(trades, orderbooks)
    event_path = root / "sessions" / "live_micro" / session_id / "forward_paper_events.jsonl"
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()] if event_path.exists() else []
    summary = {"session_id": session_id, "trade_event_count": len(trades), "orderbook_event_count": len(orderbooks), "event_count": len(events), "quality": quality, "replay_status": "REPLAYED"}
    out_root = Path(output_dir)
    if not out_root.is_absolute():
        out_root = root.parent / out_root
    out = out_root / session_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "replay_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
