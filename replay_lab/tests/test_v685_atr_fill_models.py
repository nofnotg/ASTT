from __future__ import annotations

from atr_validation.conservative_fill_model import conservative_pnl
from atr_validation.neutral_fill_model import neutral_pnl
from atr_validation.optimistic_fill_model import optimistic_pnl


def test_v685_atr_fill_models_rank_positive_trade_conservatively() -> None:
    row = {"pnl_krw": 1000.0, "position_krw": 100000.0}
    assert conservative_pnl(row) < neutral_pnl(row) < optimistic_pnl(row)


def test_v685_atr_conservative_fill_worsens_loss() -> None:
    row = {"pnl_krw": -1000.0, "position_krw": 100000.0}
    assert conservative_pnl(row) < neutral_pnl(row)
