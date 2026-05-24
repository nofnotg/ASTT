from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.feedback.tradable_winner_mining_html_report_v5510 import _write_report


class TradableSourceForwardHTMLReportV5510:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        summary = _read(REPLAY_STORE_DIR / "tradable_forward" / "latest_tradable_forward_summary.json")
        full_seed = _read(REPLAY_STORE_DIR / "tradable_forward" / "full_seed_tradable_source_validation.json")
        summary = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), **summary, "full_seed_validation": full_seed}
        return _write_report(output_dir, "latest_tradable_source_forward", "Tradable Source Forward V5.5.10", summary)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
