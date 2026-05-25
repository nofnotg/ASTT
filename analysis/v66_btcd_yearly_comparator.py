from __future__ import annotations


def yearly_delta(control_return_pct: float, scenario_return_pct: float) -> float:
    return float(scenario_return_pct) - float(control_return_pct)

