from __future__ import annotations

from replay_lab.feedback.integrated_investment_report_html import IntegratedInvestmentReportHTML


class V62FullInvestmentReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        return IntegratedInvestmentReportHTML().build(output_dir)
