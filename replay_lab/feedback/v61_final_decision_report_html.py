from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class V61FinalDecisionReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_v61_final_decision_summary.json", "latest_v61_final_decision_report.html", "V6.1 Final Decision", output_dir)
