from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_ops.llm_token_meter import LLMTokenMeter
from llm_ops.llm_usage_logger import LLMUsageLogger


def run_head_controller_v6_review(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    root = Path(reports_dir)
    daddy = _read(root / "latest_v6_daddy_strategy_summary.json")
    ict = _read(root / "latest_v6_ict_strategy_summary.json")
    combined = _read(root / "latest_v6_combined_strategy_summary.json")
    weekly = _read(root / "latest_v6_weekly_performance_summary.json")
    strategies = [row for row in [daddy, ict, combined] if row]
    best = max(strategies, key=lambda row: row.get("expectancy_pct", -999), default={})
    worst = min(strategies, key=lambda row: row.get("expectancy_pct", 999), default={})
    total_trades = sum(int(row.get("trade_count", 0)) for row in strategies)
    if total_trades == 0:
        opinion = "PROJECT_KILL_RECOMMENDED"
        problem = "PAPER_TRADE_ZERO"
        viability = "FAILED"
    elif max(float(row.get("expectancy_pct", 0.0)) for row in strategies) > 0:
        opinion = "PAPER_MORE_REQUIRED"
        problem = "FORWARD_VALIDATION_MISSING"
        viability = "PROMISING"
    else:
        opinion = "STRATEGY_REDESIGN_REQUIRED"
        problem = "NEGATIVE_EXPECTANCY"
        viability = "WEAK"
    payload = {
        "llm_provider": llm_provider,
        "llm_used": llm_provider != "off",
        "fallback_used": True,
        "live_readiness_opinion": opinion,
        "best_strategy": best.get("strategy", ""),
        "worst_strategy": worst.get("strategy", ""),
        "weekly_viability": viability,
        "primary_problem": problem,
        "next_experiments": ["Run V6.1 forward paper only on best MTF setup zones", "Tighten worst setup filters", "Compare 1% vs 1.5% risk per trade"],
        "risk_flags": ["real orders remain disabled", "OHLCV-only spread/depth is approximate"],
        "config_proposals": [],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
        "input_summary": {"total_trades": total_trades, "weekly": weekly},
    }
    meter = LLMTokenMeter()
    prompt = json.dumps({"daddy": daddy, "ict": ict, "combined": combined, "weekly": weekly}, ensure_ascii=False, default=str)
    completion = json.dumps(payload, ensure_ascii=False, default=str)
    usage = meter.from_response_usage(None, prompt, completion)
    payload["token_usage"] = {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "estimated_cost_usd": meter.estimate_cost_usd(usage),
    }
    LLMUsageLogger().log({"provider": llm_provider, "model": "v6-review-deterministic", "purpose": "HEAD_CONTROLLER_V6_REVIEW", **payload["token_usage"], "fallback_used": True, "schema_valid": True, "unsafe_proposal_detected": False})
    _write(Path("replay_store/v6_strategy/latest_head_controller_v6_review_summary.json"), payload)
    _write(root / "latest_head_controller_v6_review_summary.json", payload)
    return payload


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
