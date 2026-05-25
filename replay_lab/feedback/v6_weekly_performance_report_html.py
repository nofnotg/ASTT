from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class V6WeeklyPerformanceReportHTML:
    def build(self, output_dir="docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_v6_weekly_performance_summary.json", "latest_v6_weekly_performance_report.html", "ASTT V6 Weekly Performance", output_dir)
