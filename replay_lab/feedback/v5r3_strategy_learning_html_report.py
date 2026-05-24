from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class V5R3StrategyLearningHTMLReport:
    def build(self, output_dir: str | Path = "docs/reports") -> dict[str, str]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        market = _read(out / "latest_market_regime_summary.json")
        setup = _read(out / "latest_setup_candidate_summary.json")
        scenario = _read(out / "latest_scenario_replay_summary.json")
        paper = _read(out / "latest_aggressive_paper_learning_summary.json")
        review = _read(out / "latest_llm_strategy_review_summary.json")

        summary = {
            "version": "V5.R3",
            "risk_profile": paper.get("risk_profile", "aggressive"),
            "dominant_regime": market.get("dominant_regime", "NO_TRADE"),
            "setup_candidate_count": setup.get("candidate_count", 0),
            "scenario_count": scenario.get("scenario_count", 0),
            "paper_enter_count": paper.get("paper_enter_count", 0),
            "trade_count": paper.get("trade_count", 0),
            "win_rate": paper.get("win_rate", 0.0),
            "profit_factor": paper.get("profit_factor", 0.0),
            "expectancy_pct": paper.get("expectancy_pct", 0.0),
            "total_pnl_krw": paper.get("total_pnl_krw", 0.0),
            "total_return_pct": paper.get("total_return_pct", 0.0),
            "max_drawdown_pct": paper.get("max_drawdown_pct", 0.0),
            "pnl_evaluable": paper.get("pnl_evaluable", False),
            "llm_completion_tokens": review.get("token_usage", {}).get("completion_tokens", 0),
            "llm_fallback_used": review.get("fallback_used", True),
            "live_readiness_opinion": review.get("live_readiness_opinion", "LIVE_NOT_ALLOWED"),
            "real_order_enabled": False,
            "live_order_allowed": False,
            "auto_apply_allowed": False,
        }
        (out / "latest_v5r3_strategy_learning_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        md = _markdown(summary, market, setup, scenario, paper, review)
        html_doc = _html(md, summary, market, setup, scenario, paper, review)
        (out / "latest_v5r3_strategy_learning_report.md").write_text(md, encoding="utf-8")
        (out / "latest_v5r3_strategy_learning_report.html").write_text(html_doc, encoding="utf-8")
        return {
            "summary": str(out / "latest_v5r3_strategy_learning_summary.json"),
            "markdown": str(out / "latest_v5r3_strategy_learning_report.md"),
            "html": str(out / "latest_v5r3_strategy_learning_report.html"),
        }


def _markdown(
    summary: dict[str, Any],
    market: dict[str, Any],
    setup: dict[str, Any],
    scenario: dict[str, Any],
    paper: dict[str, Any],
    review: dict[str, Any],
) -> str:
    return "\n".join(
        [
            "# ASTT V5.R3 Strategy Learning Report",
            "",
            "## Conclusion",
            f"- Live readiness: {summary['live_readiness_opinion']}",
            f"- Paper trades: {summary['trade_count']}",
            f"- PnL evaluable: {summary['pnl_evaluable']}",
            f"- Real orders enabled: {summary['real_order_enabled']}",
            "",
            "## Market Regime",
            f"- Dominant regime: {summary['dominant_regime']}",
            f"- BTC return pct: {market.get('btc_return_pct', 0.0)}",
            f"- Breadth up ratio: {market.get('breadth_up_ratio', 0.0)}",
            "",
            "## Setup Candidates",
            f"- Candidate count: {summary['setup_candidate_count']}",
            f"- By setup: {json.dumps(setup.get('by_setup_type', {}), ensure_ascii=False)}",
            "",
            "## Scenario Replay",
            f"- Scenario count: {summary['scenario_count']}",
            f"- Scenario types: {json.dumps(scenario.get('by_scenario_type', {}), ensure_ascii=False)}",
            "",
            "## Aggressive Paper Learning",
            f"- Enter count: {summary['paper_enter_count']}",
            f"- Win rate: {summary['win_rate']}",
            f"- Profit factor: {summary['profit_factor']}",
            f"- Expectancy pct: {summary['expectancy_pct']}",
            f"- Total PnL KRW: {summary['total_pnl_krw']}",
            f"- Total return pct: {summary['total_return_pct']}",
            f"- Max drawdown pct: {summary['max_drawdown_pct']}",
            "",
            "## LLM Strategy Review",
            f"- Completion tokens: {summary['llm_completion_tokens']}",
            f"- Fallback used: {summary['llm_fallback_used']}",
            f"- Primary problem: {review.get('primary_problem', 'UNKNOWN')}",
            f"- Next experiments: {json.dumps(review.get('next_experiments', []), ensure_ascii=False)}",
            "",
            "## Safety",
            "- real_order_enabled: false",
            "- live_order_allowed: false",
            "- auto_apply_allowed: false",
        ]
    )


def _html(
    md: str,
    summary: dict[str, Any],
    market: dict[str, Any],
    setup: dict[str, Any],
    scenario: dict[str, Any],
    paper: dict[str, Any],
    review: dict[str, Any],
) -> str:
    cards = {
        "summary": summary,
        "market_regime": market,
        "setup_candidates": setup,
        "scenario_replay": scenario,
        "aggressive_paper": paper,
        "llm_strategy_review": review,
    }
    body = "\n".join(
        f"<section><h2>{html.escape(name)}</h2><pre>{html.escape(json.dumps(value, ensure_ascii=False, indent=2, default=str))}</pre></section>"
        for name, value in cards.items()
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>ASTT V5.R3 Strategy Learning Report</title>"
        "<style>body{font-family:Arial,sans-serif;margin:32px;color:#1f2937}"
        "section{border-top:1px solid #ddd;padding:18px 0}pre{background:#f6f8fa;padding:14px;overflow:auto}"
        ".lead{font-size:18px;font-weight:700}</style></head><body>"
        "<h1>ASTT V5.R3 Strategy Learning Report</h1>"
        f"<p class='lead'>Live readiness: {html.escape(str(summary.get('live_readiness_opinion')))}</p>"
        f"{body}<hr><pre>{html.escape(md)}</pre></body></html>"
    )


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))
