from __future__ import annotations

from head_controller.head_controller_proposal import build_config_proposal
from head_controller.head_controller_safety_guard import enforce_head_controller_safety
from head_controller.head_controller_schema import build_controller_output


def analyze_head_controller_context(context: dict) -> dict:
    summary = context.get("session_summary", {})
    discovery = context.get("entry_discovery", {})
    if summary.get("trade_count", 0) == 0:
        primary = "ENTER_0"
        risks = ["NO_REALISTIC_TRADES", "PNL_NOT_EVALUABLE"]
        experiments = ["Analyze MISSED_WIN WAIT paths", "Run BALANCED vs ENTRY_DISCOVERY profile with research-only guard", "Collect more UPBIT_WS sessions around high volatility"]
        proposals = [build_config_proposal("BALANCED_RESEARCH", "Evaluate whether missed WAIT paths justify a stricter balanced gate")]
    else:
        primary = "COST_SURVIVAL"
        risks = ["REALISTIC_1_REQUIRED"]
        experiments = ["Run cost survival with realistic_1 and realistic_2"]
        proposals = []
    if discovery.get("entry_discovery_enter", 0) > 0:
        experiments.append("Inspect ENTRY_DISCOVERY winners manually before any config promotion")
    output = build_controller_output(primary, experiments, risks, proposals)
    output["llm_config"] = context.get("llm_config", {"llm_enabled": False, "selected_provider": "off"})
    if output["llm_config"].get("llm_enabled"):
        output["risk_flags"].append("LLM_RESEARCH_ASSIST_ONLY")
    return enforce_head_controller_safety(output)
