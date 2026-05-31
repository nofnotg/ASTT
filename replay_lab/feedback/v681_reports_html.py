from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


class V681ReportsHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.root = Path(reports_dir)

    def build_reconciliation(self) -> dict[str, str]:
        return self._build("latest_v681_reconciliation_audit_summary.json", "latest_v681_reconciliation_audit_report.html", "V6.8.1 Ledger Reconciliation", _reconciliation_body)

    def build_compounding_dominance(self) -> dict[str, str]:
        return self._build("latest_v681_compounding_dominance_summary.json", "latest_v681_compounding_dominance_report.html", "V6.8.1 Strongest Compounding + Dominance", _scenario_body)

    def build_bear_agent(self) -> dict[str, str]:
        return self._build("latest_v681_bear_compounding_agent_summary.json", "latest_v681_bear_compounding_agent_report.html", "V6.8.1 Bear Compounding Agents", _scenario_body)

    def build_router(self) -> dict[str, str]:
        return self._build("latest_v681_compounding_router_summary.json", "latest_v681_compounding_router_report.html", "V6.8.1 Compounding Scenario Router", _scenario_body)

    def build_control_tower(self) -> dict[str, str]:
        return self._build("latest_v681_control_tower_summary.json", "latest_v681_control_tower_report.html", "V6.8.1 Paper Control Tower", _control_body)

    def build_paper_runtime(self) -> dict[str, str]:
        return self._build("latest_v681_paper_runtime_summary.json", "latest_v681_paper_runtime_report.html", "V6.8.1 Paper Runtime", _paper_body)

    def _build(self, summary_name: str, html_name: str, title: str, body_fn) -> dict[str, str]:
        payload = _read(self.root / summary_name)
        path = self.root / html_name
        path.write_text(_layout(title, body_fn(payload)), encoding="utf-8")
        return {"html": str(path), "summary": str(self.root / summary_name)}


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title>
<style>
body{{margin:0;background:#f6f7f9;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}header{{background:#111827;color:#fff;padding:28px 22px}}main{{max-width:1280px;margin:auto;padding:22px}}section,.card{{background:#fff;border:1px solid #d8dee8;border-radius:8px;padding:16px;margin:14px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.kpi{{font-size:24px;font-weight:800;margin-top:4px}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#f2f4f7}}.wrap{{overflow-x:auto}}.good{{color:#047857}}.bad{{color:#b42318}}.muted{{color:#667085}}.notice{{border-left:5px solid #b45309;background:#fffbeb}}
</style></head><body><header><h1>{_esc(title)}</h1><p>No live orders. Paper/research only.</p></header><main>{body}</main></body></html>"""


def _reconciliation_body(payload: dict[str, Any]) -> str:
    baseline = payload.get("strongest_baseline", {})
    return f"""
<section class="notice"><h2>결론</h2><p><strong>{_esc(payload.get('conclusion'))}</strong></p><p>{_esc(payload.get('reason'))}</p></section>
<section><h2>STRONGEST_COMPOUNDING_BASELINE</h2><div class="grid">
{_card('Rolling', _money(baseline.get('rolling', {}).get('final_equity_krw')), _pct(baseline.get('rolling', {}).get('return_pct')))}
{_card('Balanced', _money(baseline.get('balanced', {}).get('final_equity_krw')), _pct(baseline.get('balanced', {}).get('return_pct')))}
</div></section>
<section><h2>감사 표</h2>{_table(payload.get('comparison_items', []), ['item','v64_compounding','v673_dominance','comparable'])}</section>
"""


def _scenario_body(payload: dict[str, Any]) -> str:
    rows = payload.get("scenarios", [])
    saved = payload.get("saved_loss_missed_profit", [])
    return f"""
<section class="notice"><h2>판정</h2><p><strong>{_esc(payload.get('decision'))}</strong></p><p>real_order_enabled=false / live_order_allowed=false / auto_apply_allowed=false</p></section>
<section><h2>시나리오 비교</h2>{_table(rows, ['scenario','final_equity_krw','return_pct','mdd_pct','profit_factor','return_mdd_ratio','saved_loss_krw','missed_profit_krw','net_effect_krw','decision'])}</section>
<section><h2>Saved Loss / Missed Profit</h2>{_table(saved, ['scenario','saved_loss_krw','missed_profit_krw','net_effect_krw'])}</section>
<section><h2>Lookahead Audit</h2>{_table([payload.get('lookahead_audit', {})], ['checked_trades','pass','fail','major_violations'])}</section>
"""


def _control_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Control Tower</h2><p>active change applied: <strong>{_esc(payload.get('active_change_applied'))}</strong>, manual switch required: <strong>{_esc(payload.get('manual_switch_required'))}</strong></p></section>
<section><h2>Candidate Routes</h2>{_table(payload.get('candidate_routes', []), ['route','status','reason'])}</section>
<section><h2>Rebalance Candidates</h2>{_table(payload.get('rebalance_candidates', []), ['route','candidate_type','status'])}</section>
<section><h2>Risk Flags</h2><pre>{_esc(json.dumps(payload.get('risk_flags', []), ensure_ascii=False, indent=2))}</pre></section>
"""


def _paper_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Paper Runtime</h2><p><strong>{_esc(payload.get('decision'))}</strong> / { _esc(payload.get('healthcheck'))}</p></section>
<section><h2>상태</h2>{_table([payload], ['active_route','start_date','current_equity_krw','current_cash_krw','open_positions','today_pnl_krw','weekly_pnl_krw','monthly_pnl_krw','live_forward_running'])}</section>
<section><h2>월 단위 Paper 기록</h2>{_table(payload.get('monthly_rows', []), ['period','trade_count','start_equity_krw','end_equity_krw','pnl_krw','return_pct','mdd_pct'])}</section>
<section><h2>Shadow Routes</h2><pre>{_esc(json.dumps(payload.get('shadow_routes', []), ensure_ascii=False, indent=2))}</pre></section>
"""


def _card(label: str, value: str, sub: str = "") -> str:
    return f"<div class='card'><div>{_esc(label)}</div><div class='kpi'>{value}</div><div class='muted'>{sub}</div></div>"


def _table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return "<p class='muted'>데이터 없음</p>"
    head = "".join(f"<th>{_esc(_label(key))}</th>" for key in keys)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{_display(row.get(key), key)}</td>" for key in keys) + "</tr>"
    return f"<div class='wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _label(key: str) -> str:
    labels = {
        "scenario": "Scenario",
        "final_equity_krw": "Final Equity",
        "return_pct": "Return %",
        "mdd_pct": "MDD %",
        "profit_factor": "PF",
        "return_mdd_ratio": "Return/MDD",
        "saved_loss_krw": "Saved Loss",
        "missed_profit_krw": "Missed Profit",
        "net_effect_krw": "Net Effect",
        "decision": "Decision",
        "current_equity_krw": "Equity",
        "current_cash_krw": "Cash",
    }
    return labels.get(key, key)


def _display(value: Any, key: str) -> str:
    if value is None:
        return "N/A"
    if key.endswith("_krw") or key in {"saved_loss_krw", "missed_profit_krw", "net_effect_krw"}:
        return _money(value)
    if key.endswith("_pct") or key in {"return_pct", "mdd_pct"}:
        return _pct(value)
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "예" if value else "아니오"
    return _esc(value)


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.0f}원"
    except (TypeError, ValueError):
        return "N/A"


def _pct(value: Any) -> str:
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)
