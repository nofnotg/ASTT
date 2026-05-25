from __future__ import annotations

import json
from pathlib import Path

from market_data.ohlcv_coverage_reporter import build_ohlcv_coverage
from portfolio.full_investment_report_builder import build_full_investment_summary
from portfolio.trade_journal_builder import build_trade_journal
from portfolio.weekly_report_builder import build_weekly_rows
from portfolio.monthly_report_builder import build_monthly_rows


def run_v62_capital_growth_backtest(initial_cash_krw: float = 500000, compounding: bool = True, use_available_history: bool = True) -> dict:
    journal_summary = build_trade_journal(initial_cash_krw, compounding)
    journal = journal_summary["journal"]
    coverage = build_ohlcv_coverage("replay_store/v6_ohlcv", 36)
    weekly = {"schema_version": "v6.2", "weekly_rows": build_weekly_rows(journal), "real_order_enabled": False, "live_order_allowed": False}
    monthly = {"schema_version": "v6.2", "monthly_rows": build_monthly_rows(journal), "real_order_enabled": False, "live_order_allowed": False}
    full = build_full_investment_summary(journal, initial_cash_krw)
    full["coverage"] = coverage
    full["use_available_history"] = use_available_history
    _write("docs/reports/latest_v62_trade_journal_summary.json", journal_summary)
    _write("docs/reports/latest_v62_weekly_summary.json", weekly)
    _write("docs/reports/latest_v62_monthly_summary.json", monthly)
    _write("docs/reports/latest_v62_full_investment_summary.json", full)
    _write("replay_store/v62/latest_v62_trade_journal_summary.json", journal_summary)
    _write("replay_store/v62/latest_v62_full_investment_summary.json", full)
    return full


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
