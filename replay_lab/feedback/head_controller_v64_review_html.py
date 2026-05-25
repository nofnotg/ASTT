from __future__ import annotations

from replay_lab.feedback.v64_common_html import build_v64_html_report


class HeadControllerV64ReviewHTML:
    def build(self, reports_dir: str = "docs/reports") -> dict[str, str]:
        return build_v64_html_report("ASTT Head Controller V6.4 Review", f"{reports_dir}/latest_head_controller_v64_review_summary.json", f"{reports_dir}/latest_head_controller_v64_review_report.html", "LLM 자동 적용 없이 안전 제약과 다음 실험을 요약합니다.")
