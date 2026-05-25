from __future__ import annotations

from replay_lab.feedback.v6_report_common import build_json_html_report


class HeadControllerV61ReviewHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        return build_json_html_report("latest_head_controller_v61_review_summary.json", "latest_head_controller_v61_review_report.html", "Head Controller V6.1 Review", output_dir)
