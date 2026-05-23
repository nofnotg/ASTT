from __future__ import annotations

import json

from execution.micro_entry_gate_ab_test import run_micro_entry_gate_abtest
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.micro_entry_gate_decomposition_v554 import diagnose_micro_entry_gates_v554


def run_micro_entry_gate_abtest_v554(start_date=None, end_date=None, top_markets: int = 30, max_candidates: int = 50) -> dict:
    diagnostics = diagnose_micro_entry_gates_v554(start_date, end_date, top_markets=top_markets, max_candidates=max_candidates)
    result = run_micro_entry_gate_abtest(diagnostics.get("diagnostics", []))
    result["period"] = {"start_date": str(start_date), "end_date": str(end_date)}
    out = REPLAY_STORE_DIR / "reports" / "micro_entry_diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "gate_abtest_v554.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
