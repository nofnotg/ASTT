from __future__ import annotations

from replay_lab.feedback.v62_investor_html_common import read_json, write_investor_html


class V62FullInvestmentReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        payload = read_json(f"{output_dir}/latest_v62_full_investment_summary.json")
        return write_investor_html("V6.2 Full Investment Report", payload, f"{output_dir}/latest_v62_full_investment_report.html", payload.get("strategy_contribution", []))
