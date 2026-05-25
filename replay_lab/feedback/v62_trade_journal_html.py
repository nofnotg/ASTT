from __future__ import annotations

from replay_lab.feedback.v62_investor_html_common import read_json, write_investor_html


class V62TradeJournalHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        payload = read_json(f"{output_dir}/latest_v62_trade_journal_summary.json")
        return write_investor_html("V6.2 Trade Journal", payload, f"{output_dir}/latest_v62_trade_journal_report.html", payload.get("journal", []))
