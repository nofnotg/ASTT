from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


class V684ReportsHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.root = Path(reports_dir)

    def build_bear_windows(self) -> dict[str, str]:
        return self._build("latest_v684_bear_windows_summary.json", "latest_v684_bear_windows_report.html", "V6.8.4 Bear Windows", _bear_windows_body)

    def build_indicator_effectiveness(self) -> dict[str, str]:
        return self._build("latest_v684_indicator_effectiveness_summary.json", "latest_v684_indicator_effectiveness_report.html", "V6.8.4 Indicator Effectiveness", _indicator_body)

    def build_loss_guard_indicator(self) -> dict[str, str]:
        return self._build("latest_v684_loss_guard_indicator_lab_summary.json", "latest_v684_loss_guard_indicator_lab_report.html", "V6.8.4 Loss Guard Indicator Lab", _loss_guard_body)

    def build_bear_bounce_v3(self) -> dict[str, str]:
        return self._build("latest_v684_bear_bounce_v3_summary.json", "latest_v684_bear_bounce_v3_report.html", "V6.8.4 Bear Bounce V3", _bounce_body)

    def build_risk_sizing(self) -> dict[str, str]:
        return self._build("latest_v684_risk_sizing_lab_summary.json", "latest_v684_risk_sizing_lab_report.html", "V6.8.4 Risk Sizing Lab", _risk_body)

    def build_bear_router(self) -> dict[str, str]:
        return self._build("latest_v684_bear_router_summary.json", "latest_v684_bear_router_report.html", "V6.8.4 Bear Router", _router_body)

    def build_dashboard(self) -> dict[str, str]:
        path = self.root / "astt_report_dashboard.html"
        existing = path.read_text(encoding="utf-8-sig") if path.exists() else _layout("ASTT Report Dashboard", "")
        block = _dashboard_block()
        if "V6.8.4 Bear Indicator Validation" not in existing:
            existing = existing.replace("</main>", block + "</main>") if "</main>" in existing else existing + block
        path.write_text(existing, encoding="utf-8")
        return {"html": str(path)}

    def _build(self, summary_name: str, html_name: str, title: str, body_fn) -> dict[str, str]:
        payload = _read(self.root / summary_name)
        path = self.root / html_name
        path.write_text(_layout(title, body_fn(payload)), encoding="utf-8")
        return {"html": str(path), "summary": str(self.root / summary_name)}


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title>
<style>
body{{margin:0;background:#f7f8fb;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}header{{background:#111827;color:white;padding:28px 22px}}main{{max-width:1280px;margin:auto;padding:22px}}section,.card{{background:white;border:1px solid #d8dee8;border-radius:8px;padding:16px;margin:14px 0}}.notice{{border-left:5px solid #b45309;background:#fffbeb}}.wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#f2f4f7}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.kpi{{font-size:22px;font-weight:800}}.muted{{color:#667085}}a{{color:#1d4ed8}}
</style></head><body><header><h1>{_esc(title)}</h1><p>Research/shadow only. Live orders disabled.</p></header><main>{body}</main></body></html>"""


def _bear_windows_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Status</h2><p>{_esc(payload.get("decision"))} / windows={_esc(payload.get("window_count"))}</p></section>
<section><h2>Bear Windows</h2>{_table(payload.get("windows", []), ["window","start_time","end_time","trigger_reason","active_route_pnl","active_route_mdd","PF20","monthly_return_pct","HWM_drawdown","BTC_trend","dominance_regime","market_state","recommended_test_group"])}</section>
"""


def _indicator_body(payload: dict[str, Any]) -> str:
    return f"<section><h2>Indicator Effectiveness</h2>{_table(payload.get('indicators', []), ['indicator','risk_on_pnl','risk_off_pnl','false_alarm','saved_loss','missed_profit','net_effect','decision'])}</section>"


def _loss_guard_body(payload: dict[str, Any]) -> str:
    return f"<section><h2>Loss Guard Combinations</h2>{_table(payload.get('scenarios', []), ['scenario','final_equity_krw','return_pct','mdd_pct','profit_factor','saved_loss_krw','missed_profit_krw','net_effect_krw','decision'])}</section>"


def _bounce_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Scenario</h2>{_table([payload.get('scenario', {})], ['scenario','final_equity_krw','return_pct','mdd_pct','profit_factor','bounce_candidates','bounce_entries','decision'])}</section>
<section><h2>Bounce Types</h2>{_table(payload.get('bounce_types', []), ['bounce_type','candidates','entries','win_rate','net_pnl','avg_hold','TP','SL','decision'])}</section>
<section><h2>Best Cases</h2>{_table(payload.get('best_cases', []), ['trade_id','date','market','bounce_type','score','pnl_krw','lookahead_check'])}</section>
<section><h2>Worst Cases</h2>{_table(payload.get('worst_cases', []), ['trade_id','date','market','bounce_type','score','pnl_krw','lookahead_check'])}</section>
"""


def _risk_body(payload: dict[str, Any]) -> str:
    return f"<section><h2>Risk Sizing</h2>{_table(payload.get('models', []), ['scenario','final_equity_krw','mdd_pct','hwm_giveback_krw','hwm_giveback_pct','return_mdd_ratio','decision'])}</section>"


def _router_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Router</h2><p>{_esc(payload.get('decision'))} / active_change_applied={_esc(payload.get('active_route_change_applied'))}</p></section>
<section><h2>Scenario Results</h2>{_table(payload.get('scenarios', []), ['scenario','final_equity_krw','return_pct','mdd_pct','return_2025_pct','return_2026_pct','decision'])}</section>
<section><h2>Rules</h2>{_table(payload.get('routing_rules', []), ['market_state','route','cap'])}</section>
"""


def _dashboard_block() -> str:
    links = [
        ("Bear Windows", "latest_v684_bear_windows_report.html"),
        ("Indicator Effectiveness", "latest_v684_indicator_effectiveness_report.html"),
        ("Loss Guard Indicator", "latest_v684_loss_guard_indicator_lab_report.html"),
        ("Bear Bounce V3", "latest_v684_bear_bounce_v3_report.html"),
        ("Risk Sizing", "latest_v684_risk_sizing_lab_report.html"),
        ("Bear Router", "latest_v684_bear_router_report.html"),
    ]
    body = " / ".join(f"<a href='{href}'>{_esc(label)}</a>" for label, href in links)
    return f"<section><h2>V6.8.4 Bear Indicator Validation</h2><p>{body}</p></section>"


def _table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return "<p class='muted'>No data</p>"
    head = "".join(f"<th>{_esc(key)}</th>" for key in keys)
    body = "".join("<tr>" + "".join(f"<td>{_display(row.get(key), key)}</td>" for key in keys) + "</tr>" for row in rows)
    return f"<div class='wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _display(value: Any, key: str) -> str:
    if value is None:
        return "N/A"
    if key.endswith("_krw") or key in {"active_route_pnl", "risk_on_pnl", "risk_off_pnl", "saved_loss", "missed_profit", "net_effect", "net_pnl", "pnl_krw"}:
        return _money(value)
    if key.endswith("_pct") or key in {"active_route_mdd", "monthly_return_pct", "HWM_drawdown", "mdd_pct", "return_pct", "return_2025_pct", "return_2026_pct", "win_rate"}:
        return _pct(value)
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, (list, dict)):
        return _esc(json.dumps(value, ensure_ascii=False))
    return _esc(value)


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.0f} KRW"
    except (TypeError, ValueError):
        return str(value)


def _pct(value: Any) -> str:
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)
