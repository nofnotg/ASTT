from __future__ import annotations

from replay_lab.feedback.v64_common_html import build_v64_html_report


class V64InvestorSummaryHTMLReport:
    def build(self, reports_dir: str = "docs/reports") -> dict[str, str]:
        return build_v64_html_report("ASTT V6.4 Investor Summary", f"{reports_dir}/latest_v64_investor_summary.json", f"{reports_dir}/latest_v64_investor_report.html", "비전문가 투자자가 볼 수 있게 V6.4 결론을 요약합니다.")
