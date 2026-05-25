from __future__ import annotations

from analysis.capital_growth_analyzer import summarize_capital_growth
from analysis.risk_evidence_reporter import build_risk_evidence
from analysis.setup_context_improvement_analyzer import analyze_setup_context_improvement
from analysis.strategy_contribution_analyzer import analyze_strategy_contribution
from portfolio.monthly_report_builder import build_monthly_rows
from portfolio.seed_growth_analyzer import build_equity_curve
from portfolio.weekly_report_builder import build_weekly_rows
from strategy_router.plan_performance_analyzer import analyze_plan_performance


def build_full_investment_summary(journal: list[dict], initial_cash_krw: float = 500000) -> dict:
    return {
        "schema_version": "v6.2",
        "capital": summarize_capital_growth(journal, initial_cash_krw),
        "weekly_rows": build_weekly_rows(journal),
        "monthly_rows": build_monthly_rows(journal),
        "equity_curve": build_equity_curve(journal),
        "strategy_contribution": analyze_strategy_contribution(journal),
        "plan_performance": analyze_plan_performance(journal),
        "risk": build_risk_evidence(journal),
        "setup_context_improvement": analyze_setup_context_improvement(journal),
        "plain_language_summary": {
            "can_it_make_money": "PAPER 기준으로 가능성은 보였지만, 실제 체결 검증 전에는 실전 불가입니다.",
            "where_strong": "ALT_ROTATION/HIGH_VOLATILITY에서 ICT/Combined setup이 강했습니다.",
            "where_weak": "CHOP, Daddy 단독 신호, follow-through 부족 구간은 약했습니다.",
            "big_win_dependency": "큰 승리 의존은 존재하므로 forward paper에서 반복성을 봐야 합니다.",
        },
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
