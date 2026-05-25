from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class HeadControllerV6ReviewHTML:
    def build(self, output_dir="docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_head_controller_v6_review_summary.json", "latest_head_controller_v6_review_report.html", "ASTT Head Controller V6 Review", output_dir)
