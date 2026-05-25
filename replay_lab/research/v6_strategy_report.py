from __future__ import annotations

from replay_lab.feedback.v6_combined_strategy_report_html import V6CombinedStrategyReportHTML
from replay_lab.feedback.v6_daddy_strategy_report_html import V6DaddyStrategyReportHTML
from replay_lab.feedback.v6_ict_strategy_report_html import V6ICTStrategyReportHTML
from replay_lab.feedback.v6_mtf_report_html import V6MTFReportHTML
from replay_lab.feedback.v6_weekly_performance_report_html import V6WeeklyPerformanceReportHTML


def build_all_v6_strategy_reports() -> list[dict]:
    return [
        V6MTFReportHTML().build(),
        V6DaddyStrategyReportHTML().build(),
        V6ICTStrategyReportHTML().build(),
        V6CombinedStrategyReportHTML().build(),
        V6WeeklyPerformanceReportHTML().build(),
    ]
