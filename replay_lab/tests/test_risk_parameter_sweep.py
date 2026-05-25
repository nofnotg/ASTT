from __future__ import annotations

from analysis.risk_parameter_sweep import run_risk_parameter_sweep_rows


def test_risk_parameter_sweep_generates_grid():
    rows = run_risk_parameter_sweep_rows([{"strategy": "S", "trade_count": 2, "total_return_pct": 1, "max_drawdown_pct": -1, "profit_factor": 2}])
    assert len(rows) == 20
    assert rows[0]["decision"] == "KEEP"
