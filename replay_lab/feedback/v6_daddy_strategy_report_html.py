from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class V6DaddyStrategyReportHTML:
    def build(self, output_dir="docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_v6_daddy_strategy_summary.json", "latest_v6_daddy_strategy_report.html", "ASTT V6 Daddy Strategy", output_dir)
