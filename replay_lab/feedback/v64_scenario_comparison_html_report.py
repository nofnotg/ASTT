from __future__ import annotations

from replay_lab.feedback.v64_common_html import build_v64_html_report


class V64ScenarioComparisonHTMLReport:
    def build(self, reports_dir: str = "docs/reports") -> dict[str, str]:
        return build_v64_html_report("ASTT V6.4 Scenario Comparison", f"{reports_dir}/latest_v64_scenario_comparison_summary.json", f"{reports_dir}/latest_v64_scenario_comparison_report.html", "Baseline, 방어형, 균형형, 공격형, 고위험 연구형을 같은 조건으로 비교합니다.")
