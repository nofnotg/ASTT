from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class V61RiskSweepReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_v61_risk_sweep_summary.json", "latest_v61_risk_sweep_report.html", "V6.1 Risk Sweep", output_dir)
