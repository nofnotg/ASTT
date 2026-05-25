from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class V6MTFReportHTML:
    def build(self, output_dir="docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_v6_mtf_summary.json", "latest_v6_mtf_report.html", "ASTT V6 MTF Context", output_dir)
