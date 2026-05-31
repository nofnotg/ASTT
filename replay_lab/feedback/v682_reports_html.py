from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


class V682ReportsHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.root = Path(reports_dir)

    def build_bear_defense_insight(self) -> dict[str, str]:
        return self._build(
            "latest_v682_bear_defense_insight_summary.json",
            "latest_v682_bear_defense_insight_report.html",
            "V6.8.2 Bear Defense Deep Insight",
            _defense_body,
        )

    def build_bear_bounce(self) -> dict[str, str]:
        return self._build(
            "latest_v682_bear_bounce_summary.json",
            "latest_v682_bear_bounce_report.html",
            "V6.8.2 Bear Bounce Profit Agent",
            _bounce_body,
        )

    def build_bear_response_router(self) -> dict[str, str]:
        return self._build(
            "latest_v682_bear_response_router_summary.json",
            "latest_v682_bear_response_router_report.html",
            "V6.8.2 Bear Response Router",
            _router_body,
        )

    def build_bounce_case_study(self) -> dict[str, str]:
        return self._build(
            "latest_v682_bounce_case_study_summary.json",
            "latest_v682_bounce_case_study_report.html",
            "V6.8.2 Bounce Case Study",
            _case_body,
        )

    def _build(self, summary_name: str, html_name: str, title: str, body_fn) -> dict[str, str]:
        payload = _read(self.root / summary_name)
        path = self.root / html_name
        path.write_text(_layout(title, body_fn(payload)), encoding="utf-8")
        return {"html": str(path), "summary": str(self.root / summary_name)}


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title>
<style>
body{{margin:0;background:#f7f8fb;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}header{{background:#111827;color:white;padding:28px 22px}}main{{max-width:1280px;margin:auto;padding:22px}}section,.card{{background:white;border:1px solid #d8dee8;border-radius:8px;padding:16px;margin:14px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.kpi{{font-size:24px;font-weight:800;margin-top:4px}}.muted{{color:#667085}}.notice{{border-left:5px solid #b45309;background:#fffbeb}}.wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#f2f4f7}}pre{{white-space:pre-wrap;background:#111827;color:#f9fafb;border-radius:8px;padding:12px}}
</style></head><body><header><h1>{_esc(title)}</h1><p>Paper/shadow research only. Live trading is disabled.</p></header><main>{body}</main></body></html>"""


def _defense_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Decision</h2><p><strong>{_esc(payload.get('decision'))}</strong></p><p>real_order_enabled=false / live_order_allowed=false / auto_apply_allowed=false</p></section>
<section><h2>Active Candidate vs Baseline</h2><div class="grid">
{_card("Baseline", _money(payload.get("baseline", {}).get("final_equity_krw")), _pct(payload.get("baseline", {}).get("return_pct")))}
{_card("LG V2 + Dominance Gate", _money(payload.get("active_candidate", {}).get("final_equity_krw")), _pct(payload.get("active_candidate", {}).get("return_pct")))}
{_card("Active MDD", _pct(payload.get("active_candidate", {}).get("mdd_pct")), "lower damage is better")}
{_card("Guard Activations", _num(payload.get("guard_activation", {}).get("guard_on_count")), "hard: " + _num(payload.get("guard_activation", {}).get("hard_guard_count")))}
</div></section>
<section><h2>Guard Activation</h2>{_table([payload.get("guard_activation", {})], ["guard_on_count","hard_guard_count","guard_on_pnl_krw","hard_guard_pnl_krw","non_plan_a_guard_count","plan_a_guard_count","dominance_risk_guard_count"])}</section>
<section><h2>Sensitivity Ranking</h2>{_table(payload.get("sensitivity_rows", [])[:30], ["scenario","final_equity_krw","return_pct","mdd_pct","profit_factor","return_mdd_ratio","skipped_trade_count","average_multiplier"])}</section>
"""


def _bounce_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Decision</h2><p><strong>{_esc(payload.get('decision'))}</strong></p></section>
<section><h2>Bounce Metrics</h2>{_table([payload.get("bounce_metrics", {})], ["bounce_candidates","bounce_entries","bounce_win_rate_pct","avg_bounce_pnl_krw","net_bounce_pnl_krw","best_bounce_krw","worst_bounce_krw","tp_count","sl_count","time_stop_count"])}</section>
<section><h2>Scenario</h2>{_table([payload.get("scenario", {})], ["scenario","final_equity_krw","return_pct","mdd_pct","profit_factor","return_mdd_ratio","trade_count","skipped_trade_count","lookahead_fail_count"])}</section>
<section><h2>Best Bounce Cases</h2>{_table(payload.get("best_bounce_cases", []), ["trade_id","date","market","market_state","plan","score","pnl_krw","lookahead_check"])}</section>
<section><h2>Worst Bounce Cases</h2>{_table(payload.get("worst_bounce_cases", []), ["trade_id","date","market","market_state","plan","score","pnl_krw","lookahead_check"])}</section>
<section><h2>False Bounce Cases</h2>{_table(payload.get("false_bounce_cases", []), ["trade_id","date","market","market_state","plan","score","pnl_krw","lookahead_check"])}</section>
"""


def _router_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Decision</h2><p><strong>{_esc(payload.get('decision'))}</strong></p><p>Active route change applied: <strong>{_esc(payload.get('active_route_change_applied'))}</strong></p></section>
<section><h2>Scenario Comparison</h2>{_table(payload.get("scenarios", []), ["scenario","final_equity_krw","return_pct","mdd_pct","profit_factor","return_mdd_ratio","return_2025_pct","return_2026_pct","saved_loss_krw","missed_profit_krw","net_effect_krw","bounce_trade_count","profit_giveback_ratio_pct","decision"])}</section>
<section><h2>Route Usage</h2><pre>{_esc(json.dumps(payload.get("route_usage_count", {}), ensure_ascii=False, indent=2))}</pre></section>
<section><h2>Bounce Metrics by Scenario</h2>{_table([{"scenario": key, **value} for key, value in payload.get("bounce_metrics", {}).items()], ["scenario","bounce_candidates","bounce_entries","bounce_win_rate_pct","net_bounce_pnl_krw","best_bounce_krw","worst_bounce_krw"])}</section>
"""


def _case_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Decision</h2><p><strong>{_esc(payload.get('decision'))}</strong></p></section>
<section><h2>Best Bounce 10</h2>{_table(payload.get("best_bounce_cases", []), ["trade_id","date","market","market_state","plan","score","pnl_krw","lookahead_check"])}</section>
<section><h2>Worst Bounce 10</h2>{_table(payload.get("worst_bounce_cases", []), ["trade_id","date","market","market_state","plan","score","pnl_krw","lookahead_check"])}</section>
<section><h2>Missed Bounce 10</h2>{_table(payload.get("missed_bounce_cases", []), ["trade_id","date","market","market_state","plan","score","pnl_krw","lookahead_check"])}</section>
<section><h2>False Bounce 10</h2>{_table(payload.get("false_bounce_cases", []), ["trade_id","date","market","market_state","plan","score","pnl_krw","lookahead_check"])}</section>
"""


def _card(label: str, value: str, sub: str = "") -> str:
    return f"<div class='card'><div>{_esc(label)}</div><div class='kpi'>{value}</div><div class='muted'>{_esc(sub)}</div></div>"


def _table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return "<p class='muted'>No data</p>"
    head = "".join(f"<th>{_esc(_label(key))}</th>" for key in keys)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{_display(row.get(key), key)}</td>" for key in keys) + "</tr>"
    return f"<div class='wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _label(key: str) -> str:
    return {
        "scenario": "Scenario",
        "final_equity_krw": "Final Equity",
        "return_pct": "Return",
        "mdd_pct": "MDD",
        "profit_factor": "PF",
        "return_mdd_ratio": "Return/MDD",
        "pnl_krw": "PnL",
        "net_bounce_pnl_krw": "Net Bounce PnL",
    }.get(key, key)


def _display(value: Any, key: str) -> str:
    if value is None:
        return "N/A"
    if key.endswith("_krw") or key in {"pnl_krw", "saved_loss_krw", "missed_profit_krw", "net_effect_krw"}:
        return _money(value)
    if key.endswith("_pct") or key in {"return_pct", "mdd_pct"}:
        return _pct(value)
    if isinstance(value, float):
        return f"{value:.3f}"
    return _esc(value)


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.0f} KRW"
    except (TypeError, ValueError):
        return "N/A"


def _pct(value: Any) -> str:
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def _num(value: Any) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "N/A"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)
