from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.feedback.tradable_winner_mining_html_report_v5510 import _write_report


class HighVolatilitySessionHTMLReportV5510:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        summary = _read(REPLAY_STORE_DIR / "live_v5510" / "latest_live_session_summary.json")
        summary = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), **summary}
        return _write_report(output_dir, "latest_high_volatility_session", "High Volatility Session V5.5.10", summary)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"quality": "NO_DATA", "trade_event_count": 0, "orderbook_event_count": 0, "ticker_event_count": 0, "real_order_enabled": False}
