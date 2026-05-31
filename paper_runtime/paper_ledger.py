from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PaperLedgerState:
    equity_krw: float
    cash_krw: float
    open_positions: int = 0


def initial_ledger(initial_cash_krw: float) -> PaperLedgerState:
    return PaperLedgerState(equity_krw=float(initial_cash_krw), cash_krw=float(initial_cash_krw), open_positions=0)


def ledger_from_journal(journal: list[dict[str, Any]], initial_cash_krw: float) -> PaperLedgerState:
    if not journal:
        return initial_ledger(initial_cash_krw)
    equity = float(journal[-1].get("equity_after", initial_cash_krw))
    return PaperLedgerState(equity_krw=equity, cash_krw=equity, open_positions=0)
