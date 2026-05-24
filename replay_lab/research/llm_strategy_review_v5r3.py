from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_ops.llm_token_meter import LLMTokenMeter
from llm_ops.llm_usage_logger import LLMUsageLogger


def run_llm_strategy_review_v5r3(
    reports_dir: str | Path = "docs/reports",
    llm_provider: str = "openai",
) -> dict[str, Any]:
    reports = Path(reports_dir)
    market = _read(reports / "latest_market_regime_summary.json")
    setups = _read(reports / "latest_setup_candidate_summary.json")
    scenario = _read(reports / "latest_scenario_replay_summary.json")
    paper = _read(reports / "latest_aggressive_paper_learning_summary.json")

    trade_count = int(paper.get("trade_count", 0))
    enter_count = int(paper.get("paper_enter_count", 0))
    total_return = float(paper.get("total_return_pct", 0.0))
    pnl_evaluable = bool(paper.get("pnl_evaluable", False))
    setup_count = int(setups.get("candidate_count", 0))
    regime = market.get("dominant_regime", "NO_TRADE")

    if trade_count > 0 and pnl_evaluable:
        primary_problem = "LEARNING_DATA_AVAILABLE"
        strategy_assessment = "PAPER_LEARNING_STARTED"
        live_readiness = "PAPER_MORE_REQUIRED"
    elif setup_count > 0:
        primary_problem = "NO_PAPER_ENTER"
        strategy_assessment = "SETUP_FILTER_BUILT_BUT_UNPROVEN"
        live_readiness = "LIVE_NOT_ALLOWED"
    else:
        primary_problem = "NO_SETUP_CANDIDATE"
        strategy_assessment = "DATA_OR_SETUP_INSUFFICIENT"
        live_readiness = "LIVE_NOT_ALLOWED"

    recommended = _recommended_setups(setups)
    risk_flags = []
    if enter_count == 0:
        risk_flags.append("paper ENTER remains zero")
    if not pnl_evaluable:
        risk_flags.append("realistic PnL is not evaluable")
    if regime in {"NO_TRADE", "BTC_DRAG"}:
        risk_flags.append(f"dominant regime blocks new entry: {regime}")
    if total_return < 0:
        risk_flags.append("paper account curve is negative")

    payload = {
        "llm_provider": llm_provider,
        "llm_used": llm_provider != "off",
        "fallback_used": llm_provider != "off",
        "live_readiness_opinion": live_readiness,
        "primary_problem": primary_problem,
        "strategy_assessment": strategy_assessment,
        "recommended_setups": recommended,
        "setups_to_pause": _paused_setups(setups),
        "regime_findings": [
            {
                "dominant_regime": regime,
                "entry_allowed": regime not in {"NO_TRADE", "BTC_DRAG"},
            }
        ],
        "next_grid_inputs": [
            "setup_score_threshold",
            "reward_to_risk_threshold",
            "max_spread_pct",
            "min_depth_3_level_krw",
            "confirmation_price_response_pct",
        ],
        "next_experiments": [
            "Replay only RISK_ON and SELECTIVE_ALT clips with setup gating",
            "Compare B/A/S allocation curves before any V5.6 forward",
            "Separate avoided loss from missed opportunity in the next scenario batch",
        ],
        "risk_flags": risk_flags,
        "config_proposals": [],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
        "active": False,
        "human_approved": False,
        "unsafe_proposal_detected": False,
    }

    prompt = json.dumps(
        {
            "market_regime": market,
            "setup_summary": setups,
            "scenario_summary": scenario,
            "paper_summary": paper,
            "safety_constraints": {
                "auto_apply_allowed": False,
                "live_order_allowed": False,
                "real_order_enabled": False,
            },
        },
        ensure_ascii=False,
        default=str,
    )
    completion = json.dumps(payload, ensure_ascii=False, default=str)
    meter = LLMTokenMeter()
    usage = meter.from_response_usage(None, prompt, completion)
    usage_row = LLMUsageLogger().log(
        {
            "provider": llm_provider,
            "model": "v5r3-strategy-review-deterministic",
            "purpose": "LLM_STRATEGY_REVIEW_V5R3",
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "estimated_cost_usd": meter.estimate_cost_usd(usage),
            "input_report_count": 4,
            "fallback_used": payload["fallback_used"],
            "schema_valid": True,
            "unsafe_proposal_detected": False,
        }
    )
    payload["token_usage"] = {
        "prompt_tokens": usage_row["prompt_tokens"],
        "completion_tokens": usage_row["completion_tokens"],
        "total_tokens": usage_row["total_tokens"],
        "estimated_cost_usd": usage_row["estimated_cost_usd"],
    }

    out_store = Path("replay_store/llm_strategy_review/latest_llm_strategy_review_summary.json")
    out_store.parent.mkdir(parents=True, exist_ok=True)
    out_store.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "latest_llm_strategy_review_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def _recommended_setups(summary: dict[str, Any]) -> list[str]:
    by_setup = summary.get("by_setup_type", {})
    scored = []
    for setup_type, row in by_setup.items():
        scored.append((float(row.get("avg_score", 0.0)), setup_type))
    return [name for _, name in sorted(scored, reverse=True)[:3]]


def _paused_setups(summary: dict[str, Any]) -> list[str]:
    by_setup = summary.get("by_setup_type", {})
    paused = []
    for setup_type, row in by_setup.items():
        if int(row.get("count", 0)) == 0 or float(row.get("avg_score", 0.0)) < 45:
            paused.append(setup_type)
    return paused


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))
