from __future__ import annotations

from replay_lab.feedback.v62_full_investment_report_html import V62FullInvestmentReportHTML
from replay_lab.feedback.v62_monthly_report_html import V62MonthlyReportHTML
from replay_lab.feedback.v62_risk_report_html import V62RiskReportHTML
from replay_lab.feedback.v62_strategy_router_report_html import V62StrategyRouterReportHTML
from replay_lab.feedback.v62_trade_journal_html import V62TradeJournalHTML
from replay_lab.feedback.v62_weekly_report_html import V62WeeklyReportHTML


def build_v62_investment_reports(reports_dir: str = "docs/reports") -> list[dict]:
    return [
        V62TradeJournalHTML().build(reports_dir),
        V62WeeklyReportHTML().build(reports_dir),
        V62MonthlyReportHTML().build(reports_dir),
        V62FullInvestmentReportHTML().build(reports_dir),
        V62StrategyRouterReportHTML().build(reports_dir),
        V62RiskReportHTML().build(reports_dir),
    ]
