from __future__ import annotations

from replay_lab.feedback.v62_investor_html_common import read_json, write_investor_html


class HeadControllerV62ReviewHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        payload = read_json(f"{output_dir}/latest_head_controller_v62_review_summary.json")
        return write_investor_html("Head Controller V6.2 Review", payload, f"{output_dir}/latest_head_controller_v62_review_report.html", payload.get("next_experiments", []))
