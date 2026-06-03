from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import read_jsonl, safe_status, write_html, write_json


def build_variable_convergence_analysis(
    initial_cash_krw: float = 500000.0,
    use_available_history: bool = True,
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
) -> dict[str, Any]:
    decisions = read_jsonl(Path(data_dir) / "journal" / "paper_decisions.jsonl")
    variables = ["pf20", "month_return_pct", "hwm_drawdown_pct", "dominance_risk", "guard_on", "hard_guard"]
    rows = []
    for variable in variables:
        values = [row.get(variable) for row in decisions if row.get(variable) is not None]
        rows.append(
            {
                "Variable": variable,
                "Win Correlation": None,
                "Loss Correlation": None,
                "False Skip": None,
                "False Entry": None,
                "sample_count": len(values),
                "Recommendation": "표본 축적 후 재평가" if len(values) < 30 else "계속 추적",
            }
        )
    payload = {
        "schema_version": "v688_variable_convergence_v1",
        "winning_common_variables": rows,
        "losing_common_variables": rows,
        "false_entry_variables": [],
        "false_skip_variables": [],
        "route_specific_variables": [],
        "market_state_specific_variables": [],
        "caution": "correlation과 causation을 구분해야 하며 표본 부족은 과장하지 않습니다.",
        **safe_status(),
    }
    reports = Path(reports_dir)
    write_json(reports / "latest_v688_variable_convergence_summary.json", payload)
    write_html(reports / "latest_v688_variable_convergence_report.html", "V6.8.8 Variable Convergence", [("Variable Table", rows), ("Caution", payload["caution"])])
    return payload
