from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


class V685ReportsHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.root = Path(reports_dir)

    def build_atr_precision(self) -> dict[str, str]:
        return self._build("latest_v685_atr_precision_audit_summary.json", "latest_v685_atr_precision_audit_report.html", "V6.8.5 ATR Precision Audit", _atr_precision_body)

    def build_atr_price_path(self) -> dict[str, str]:
        return self._build("latest_v685_atr_price_path_audit_summary.json", "latest_v685_atr_price_path_audit_report.html", "V6.8.5 ATR Price Path Audit", _atr_price_path_body)

    def build_atr_sensitivity(self) -> dict[str, str]:
        return self._build("latest_v685_atr_sensitivity_summary.json", "latest_v685_atr_sensitivity_report.html", "V6.8.5 ATR Sensitivity", _atr_sensitivity_body)

    def build_bear_window_classification(self) -> dict[str, str]:
        return self._build("latest_v685_bear_window_classification_summary.json", "latest_v685_bear_window_classification_report.html", "V6.8.5 Bear Window Classification", _classification_body)

    def build_bear_window_performance(self) -> dict[str, str]:
        return self._build("latest_v685_bear_window_performance_summary.json", "latest_v685_bear_window_performance_report.html", "V6.8.5 Bear Window Performance", _performance_body)

    def build_bear_router_window_aware(self) -> dict[str, str]:
        return self._build("latest_v685_bear_router_window_aware_summary.json", "latest_v685_bear_router_window_aware_report.html", "V6.8.5 Window-Aware Bear Router", _router_body)

    def build_dashboard(self) -> dict[str, str]:
        path = self.root / "astt_report_dashboard.html"
        existing = path.read_text(encoding="utf-8-sig") if path.exists() else _layout("ASTT Report Dashboard", "")
        block = _dashboard_block()
        if "V6.8.5 ATR Precision + Bear Window Performance" not in existing:
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
body{{margin:0;background:#f7f8fb;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}header{{background:#111827;color:white;padding:28px 22px}}main{{max-width:1280px;margin:auto;padding:22px}}section{{background:white;border:1px solid #d8dee8;border-radius:8px;padding:16px;margin:14px 0}}.notice{{border-left:5px solid #b45309;background:#fffbeb}}.wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#f2f4f7}}.muted{{color:#667085}}a{{color:#1d4ed8}}
</style></head><body><header><h1>{_esc(title)}</h1><p>Research/shadow only. Live orders disabled.</p></header><main>{body}</main></body></html>"""


def _atr_precision_body(payload: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>Status</h2><p>{_esc(payload.get('decision'))}</p></section><section>{_table(payload.get('scenarios', []), ['scenario','model','final_equity_krw','return_pct','mdd_pct','profit_factor','decision'])}</section>"


def _atr_price_path_body(payload: dict[str, Any]) -> str:
    return f"""
<section class='notice'><h2>Final ATR Decision</h2><p>{_esc(payload.get('final_atr_decision'))}</p></section>
<section><h2>Fill Models</h2>{_table(payload.get('fill_model_results', []), ['model','final_equity_krw','return_pct','mdd_pct','profit_factor','conflict_trades','decision'])}</section>
<section><h2>Lower Timeframe Coverage</h2>{_table([payload.get('lower_timeframe', {})], ['lower_timeframe_available','covered_trade_count','uncovered_trade_count','coverage_pct','price_path_ambiguous_count','reason'])}</section>
<section><h2>Sample Conflicts</h2>{_table(payload.get('audit_rows', [])[:50], ['trade_id','market','entry_time','atr_timeframe','bar_conflict','conflict_type','decision'])}</section>
"""


def _atr_sensitivity_body(payload: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>Warning</h2><p>{_esc(payload.get('overfit_warning'))}</p></section><section>{_table(payload.get('rows', [])[:120], ['period','multiplier','timeframe','fill_model','return_pct','mdd_pct','conflict_pct','decision'])}</section>"


def _classification_body(payload: dict[str, Any]) -> str:
    return f"<section><h2>Window Classification</h2>{_table(payload.get('windows', []), ['window_id','window_type','start_time','end_time','trigger_reason','active_route_pnl','market_state','dominance_regime','best_shadow_route','best_shadow_return_pct'])}</section>"


def _performance_body(payload: dict[str, Any]) -> str:
    return f"""
<section><h2>Window Rows</h2>{_table(payload.get('window_rows', []), ['window','type','start','end','active_return','best_route','best_return','mdd','winner','comment'])}</section>
<section><h2>Scenario Bear Window Totals</h2>{_table(payload.get('scenario_rows', []), ['scenario','bear_window_pnl','bear_window_return','bear_window_mdd','saved_loss','missed_profit','decision'])}</section>
<section><h2>Window Type Summary</h2>{_table(payload.get('window_type_summary', []), ['window_type','best_scenario','avg_return','avg_mdd','recommended_action'])}</section>
"""


def _router_body(payload: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>Status</h2><p>{_esc(payload.get('decision'))} / active_change_applied={_esc(payload.get('active_route_change_applied'))}</p></section><section>{_table(payload.get('rows', []), ['router','full_return','full_mdd','bear_window_return','bear_window_mdd','decision'])}</section><section>{_table(payload.get('route_rules', []), ['window_type','route'])}</section>"


def _dashboard_block() -> str:
    links = [
        ("ATR Precision Audit", "latest_v685_atr_precision_audit_report.html"),
        ("ATR Price Path Audit", "latest_v685_atr_price_path_audit_report.html"),
        ("ATR Sensitivity", "latest_v685_atr_sensitivity_report.html"),
        ("Bear Window Classification", "latest_v685_bear_window_classification_report.html"),
        ("Bear Window Performance", "latest_v685_bear_window_performance_report.html"),
        ("Bear Router Window-Aware", "latest_v685_bear_router_window_aware_report.html"),
    ]
    body = " / ".join(f"<a href='{href}'>{_esc(label)}</a>" for label, href in links)
    return f"<section><h2>V6.8.5 ATR Precision + Bear Window Performance</h2><p>{body}</p></section>"


def _table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return "<p class='muted'>No data</p>"
    head = "".join(f"<th>{_esc(key)}</th>" for key in keys)
    body = "".join("<tr>" + "".join(f"<td>{_display(row.get(key), key)}</td>" for key in keys) + "</tr>" for row in rows)
    return f"<div class='wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _display(value: Any, key: str) -> str:
    if value is None:
        return "N/A"
    if key.endswith("_krw") or key in {"active_route_pnl", "bear_window_pnl", "saved_loss", "missed_profit"}:
        return _money(value)
    if key.endswith("_pct") or key in {"return_pct", "mdd_pct", "coverage_pct", "conflict_pct", "best_shadow_return_pct", "active_return", "best_return", "mdd", "bear_window_return", "bear_window_mdd", "avg_return", "avg_mdd", "full_return", "full_mdd"}:
        return _pct(value)
    if isinstance(value, float):
        return f"{value:.3f}"
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
