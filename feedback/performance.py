from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import func, select

from app.config import Settings, get_settings
from data.schemas import DailyReport, PaperTrade, PersonaScore, Signal
from data.storage import Storage


def generate_daily_report(storage: Storage | None = None, settings: Settings | None = None, report_date: str | None = None) -> Path:
    settings = settings or get_settings()
    storage = storage or Storage(settings)
    report_date = report_date or date.today().isoformat()
    with storage.session() as session:
        signal_count = session.scalar(select(func.count()).select_from(Signal)) or 0
        entered_count = session.scalar(select(func.count()).select_from(Signal).where(Signal.final_decision == "ENTER")) or 0
        veto_count = session.scalar(select(func.count()).select_from(Signal).where(Signal.vetoed.is_(True))) or 0
        trades = session.execute(select(PaperTrade)).scalars().all()
        realized = sum(item.realized_pnl_krw for item in trades)
        wins = sum(1 for item in trades if item.realized_pnl_krw > 0)
        losses = sum(1 for item in trades if item.realized_pnl_krw < 0)
        persona_rows = session.execute(select(PersonaScore.persona_name, func.avg(PersonaScore.score)).group_by(PersonaScore.persona_name)).all()
    markdown_path = settings.reports_dir / f"{report_date}_daily_report.md"
    persona_lines = "\n".join(f"- {name}: {score:.2f}" for name, score in persona_rows) or "- none"
    content = f"""# ASTT Daily Report - {report_date}

## Summary
- mode: {settings.trading_mode.value}
- signal_count: {signal_count}
- entered_count: {entered_count}
- win_count: {wins}
- loss_count: {losses}
- realized_pnl_krw: {realized:.2f}
- unrealized_pnl_krw: not calculated in this report
- max_drawdown_pct: 0.00
- iris_veto_count: {veto_count}

## Persona Average Scores
{persona_lines}

## Notes
- Total asset must be read as virtual cash plus marked paper positions.
- LIVE orders remain blocked unless both LIVE safeguards are enabled.
"""
    markdown_path.write_text(content, encoding="utf-8")
    with storage.session() as session:
        session.add(
            DailyReport(
                report_date=report_date,
                signal_count=signal_count,
                entered_count=entered_count,
                win_count=wins,
                loss_count=losses,
                realized_pnl_krw=realized,
                realized_pnl_pct=0.0,
                max_drawdown_pct=0.0,
                veto_count=veto_count,
                markdown_path=str(markdown_path),
            )
        )
        session.commit()
    return markdown_path

