from __future__ import annotations


def extract_rule_summary(strategy_spec: dict) -> dict:
    return {
        "strategy_id": strategy_spec.get("strategy_id"),
        "entry_rules": strategy_spec.get("entry_rules", []),
        "exit_rules": strategy_spec.get("exit_rules", []),
        "risk_rules": strategy_spec.get("risk_rules", []),
        "micro_execution_required": strategy_spec.get("micro_execution_required", False),
    }
