from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR


class WinnerQualityFilterHTMLReportV559:
    def build(self) -> str:
        payload = json.loads((REPLAY_STORE_DIR / "winner_quality" / "quality_winners.json").read_text(encoding="utf-8"))
        summary = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), **payload["summary"]}
        docs = ROOT_DIR / "docs" / "reports"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "latest_winner_quality_filter_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md = self._markdown(summary)
        html = "<!doctype html><html><head><meta charset='utf-8'><title>Winner Quality Filter V5.5.9</title></head><body><pre>" + json.dumps(summary, ensure_ascii=False, indent=2) + "</pre></body></html>"
        (docs / "latest_winner_quality_filter_report.md").write_text(md, encoding="utf-8")
        (docs / "latest_winner_quality_filter_report.html").write_text(html, encoding="utf-8")
        return str(docs / "latest_winner_quality_filter_report.html")

    def _markdown(self, s: dict) -> str:
        return f"""# Winner Quality Filter V5.5.9

실제 거래 가능한 winner만 남기는 research report입니다.

| Metric | Value |
|---|---:|
| Raw Winners | {s.get('raw_winner_count', 0)} |
| Quality Winners | {s.get('quality_winner_count', 0)} |
| Rejected Winners | {s.get('rejected_winner_count', 0)} |
| Tick Noise Rejected | {s.get('tick_noise_count', 0)} |
| Liquidity Rejected | {s.get('insufficient_liquidity_count', 0)} |
| Spread Rejected | {s.get('spread_too_wide_count', 0)} |
| Avg Effective Return % | {s.get('effective_return_avg', 0):.4f} |
| Tradable With 500k | {s.get('tradable_with_500k_count', 0)} |
"""
