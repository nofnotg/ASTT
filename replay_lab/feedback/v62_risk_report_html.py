from __future__ import annotations

from replay_lab.feedback.v62_investor_html_common import read_json, write_investor_html


class V62RiskReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        payload = read_json(f"{output_dir}/latest_v62_risk_summary.json")
        rows = payload.get("risk", {}).get("risk_rows", [])
        return write_investor_html("V6.2 Risk Report", payload, f"{output_dir}/latest_v62_risk_report.html", rows)
