from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TERMS = [
    "btc_dominance",
    "btc_dominance_pct",
    "btcd",
    "BTC.D",
    "market_cap_percentage",
    "btc_market_cap_share",
    "upbit_btc_volume_share",
    "btc_flow_dominance",
]

TARGETS = {
    "Rolling Edge": ["analysis/v64_policy_compounding_analyzer.py", "portfolio/causal_equity_defense_runner.py"],
    "Balanced Growth": ["analysis/v64_policy_compounding_analyzer.py", "portfolio/causal_equity_defense_runner.py"],
    "Policy Blend": ["analysis/v64_policy_blend_analyzer.py"],
    "True Walk-Forward": ["portfolio/walk_forward_investment_simulator.py"],
    "V6.4 Defense": ["analysis/v64_scenario_comparator.py", "portfolio/causal_equity_defense_runner.py"],
    "V6.5 MA Scenario": ["analysis/v65_ma_scenario_analyzer.py"],
}


def audit_v66_btcd_inclusion(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root)
    evidence: list[dict[str, Any]] = []
    rows: dict[str, bool] = {}
    for scenario, files in TARGETS.items():
        found = False
        for file_name in files:
            path = root / file_name
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for term in TERMS:
                if term.lower() in text.lower():
                    found = True
                    evidence.append({"scenario": scenario, "file": file_name, "term": term})
        rows[scenario] = found
    conclusion = (
        "BTC dominance was not used in the existing validated Rolling/Balanced/Policy Blend/True Walk-Forward scenarios."
        if not any(rows.values())
        else "Some BTC dominance terms exist in audited files; inspect evidence before claiming a clean baseline."
    )
    return {
        "schema_version": "v66_btcd_inclusion_audit_v1",
        "btcd_in_existing_rolling_edge": rows.get("Rolling Edge", False),
        "btcd_in_existing_balanced_growth": rows.get("Balanced Growth", False),
        "btcd_in_policy_blend": rows.get("Policy Blend", False),
        "btcd_in_true_walk_forward": rows.get("True Walk-Forward", False),
        "btcd_in_v64_defense": rows.get("V6.4 Defense", False),
        "btcd_in_v65_ma": rows.get("V6.5 MA Scenario", False),
        "evidence": evidence,
        "conclusion": conclusion,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def write_btcd_inclusion_audit(reports_dir: str = "docs/reports", repo_root: str | Path = ".") -> dict[str, Any]:
    summary = audit_v66_btcd_inclusion(repo_root)
    path = Path(reports_dir) / "latest_v66_btcd_inclusion_audit_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary

