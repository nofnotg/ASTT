from __future__ import annotations

from replay_lab.feedback.v64_common_html import build_v64_html_report


class V64ReturnAmplificationHTMLReport:
    def build(self, reports_dir: str = "docs/reports") -> dict[str, str]:
        return build_v64_html_report("ASTT V6.4 Return Amplification Lab", f"{reports_dir}/latest_v64_return_amplification_summary.json", f"{reports_dir}/latest_v64_return_amplification_report.html", "방어를 유지한 상태에서 공격성을 높인 후보의 수익률과 위험을 비교합니다.")
