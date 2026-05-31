from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


class V683ReportsHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.root = Path(reports_dir)

    def build_backfill(self) -> dict[str, str]:
        return self._build("latest_v683_backfill_20260101_summary.json", "latest_v683_backfill_20260101_report.html", "V6.8.3 2026 Backfill", _backfill_body)

    def build_runtime(self) -> dict[str, str]:
        return self._build("latest_v683_paper_runtime_summary.json", "latest_v683_paper_runtime_report.html", "V6.8.3 Paper Runtime", _runtime_body)

    def build_active_shadow(self) -> dict[str, str]:
        return self._build("latest_v683_active_shadow_comparison_summary.json", "latest_v683_active_shadow_comparison_report.html", "V6.8.3 Active vs Shadow", _active_shadow_body)

    def build_router(self) -> dict[str, str]:
        return self._build("latest_v683_route_router_summary.json", "latest_v683_route_router_report.html", "V6.8.3 Scenario Router", _router_body)

    def build_control_tower(self) -> dict[str, str]:
        return self._build("latest_v683_control_tower_summary.json", "latest_v683_control_tower_report.html", "V6.8.3 Control Tower", _control_body)

    def build_dashboard(self) -> dict[str, str]:
        payload = {
            "runtime": _read(self.root / "latest_v683_paper_runtime_summary.json"),
            "backfill": _read(self.root / "latest_v683_backfill_20260101_summary.json"),
            "comparison": _read(self.root / "latest_v683_active_shadow_comparison_summary.json"),
            "control": _read(self.root / "latest_v683_control_tower_summary.json"),
        }
        path = self.root / "astt_report_dashboard.html"
        path.write_text(_layout("ASTT Paper Dashboard", _dashboard_body(payload)), encoding="utf-8")
        return {"html": str(path), "summary": str(self.root / "latest_v683_paper_runtime_summary.json")}

    def build_period_reports(self) -> dict[str, str]:
        backfill = _read(self.root / "latest_v683_backfill_20260101_summary.json")
        monthly = backfill.get("monthly_returns", {})
        daily_path = self.root / "latest_v683_daily_paper_report.html"
        weekly_path = self.root / "latest_v683_weekly_paper_report.html"
        monthly_path = self.root / "latest_v683_monthly_paper_report.html"
        daily_path.write_text(_layout("V6.8.3 Daily Paper", _period_body(backfill.get("daily_equity", {}))), encoding="utf-8")
        weekly_path.write_text(_layout("V6.8.3 Weekly Paper", _period_body(backfill.get("weekly_returns", {}))), encoding="utf-8")
        monthly_path.write_text(_layout("V6.8.3 Monthly Paper", _period_body(monthly)), encoding="utf-8")
        return {"daily": str(daily_path), "weekly": str(weekly_path), "monthly": str(monthly_path)}

    def _build(self, summary_name: str, html_name: str, title: str, body_fn) -> dict[str, str]:
        payload = _read(self.root / summary_name)
        path = self.root / html_name
        path.write_text(_layout(title, body_fn(payload)), encoding="utf-8")
        return {"html": str(path), "summary": str(self.root / summary_name)}


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_esc(title)}</title>
<style>
body{{margin:0;background:#f7f8fb;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}header{{background:#111827;color:white;padding:28px 22px}}main{{max-width:1280px;margin:auto;padding:22px}}section,.card{{background:white;border:1px solid #d8dee8;border-radius:8px;padding:16px;margin:14px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.kpi{{font-size:24px;font-weight:800;margin-top:4px}}.muted{{color:#667085}}.notice{{border-left:5px solid #b45309;background:#fffbeb}}.wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#f2f4f7}}pre{{white-space:pre-wrap;background:#111827;color:#f9fafb;border-radius:8px;padding:12px}}
</style></head><body><header><h1>{_esc(title)}</h1><p>Paper-only route monitoring. Live orders disabled.</p></header><main>{body}</main></body></html>"""


def _backfill_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Status</h2><p><strong>{_esc(payload.get('decision'))}</strong> / source_mode={_esc(payload.get('source_mode'))}</p></section>
<section><h2>Route Results</h2>{_table(payload.get("routes", []), ["scenario","route_status","final_equity_krw","return_pct","mdd_pct","profit_factor","trade_count","win_rate_pct","saved_loss_krw","missed_profit_krw","net_effect_krw","decision"])}</section>
<section><h2>Monthly Active vs Shadow</h2>{_table(payload.get("active_vs_shadow_monthly", []), ["month","active_route_return_pct","best_shadow_route","best_shadow_return_pct","delta_pct","comment"])}</section>
"""


def _runtime_body(payload: dict[str, Any]) -> str:
    return f"""
<section class="notice"><h2>Runtime</h2><p><strong>{_esc(payload.get('decision'))}</strong> / { _esc(payload.get('healthcheck'))}</p></section>
<section><h2>Paper Account</h2>{_table([payload], ["active_route","current_equity_krw","current_cash_krw","open_positions","paper_server_port","server_started","live_forward_running","last_decision_time","last_equity_snapshot_time"])}</section>
"""


def _active_shadow_body(payload: dict[str, Any]) -> str:
    return f"<section><h2>Active vs Shadow</h2>{_table(payload.get('rows', []), ['route','status','equity','today_pnl','weekly_pnl','monthly_pnl','mdd_pct','return_delta_vs_active_pct','comment'])}</section>"


def _router_body(payload: dict[str, Any]) -> str:
    return f"<section><h2>Router Rules</h2>{_table(payload.get('market_state_rules', []), ['market_state','action'])}</section><section>{_table([payload], ['bear_bounce_current_version','active_auto_switch_allowed','decision'])}</section>"


def _control_body(payload: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>Control Tower</h2><p>{_esc(payload.get('latest_recommendation'))}</p></section><section>{_table(payload.get('rebalance_candidates', []), ['route','candidate_type','status'])}</section><section><pre>{_esc(json.dumps(payload.get('risk_flags', []), ensure_ascii=False, indent=2))}</pre></section>"


def _dashboard_body(payload: dict[str, Any]) -> str:
    runtime = payload.get("runtime", {})
    control = payload.get("control", {})
    comparison = payload.get("comparison", {})
    return f"""
<section class="notice"><h2>Paper Server Status</h2><div class="grid">
{_card("Active Route", runtime.get("active_route"))}
{_card("Current Equity", _money(runtime.get("current_equity_krw")))}
{_card("Healthcheck", runtime.get("healthcheck"))}
{_card("Control Tower", control.get("latest_recommendation"))}
</div></section>
<section><h2>Active vs Shadow Summary</h2>{_table(comparison.get("rows", []), ["route","status","equity","mdd_pct","return_delta_vs_active_pct","comment"])}</section>
<section><h2>Reports</h2><p><a href="latest_v683_backfill_20260101_report.html">Backfill</a> / <a href="latest_v683_paper_runtime_report.html">Runtime</a> / <a href="latest_v683_active_shadow_comparison_report.html">Active vs Shadow</a> / <a href="latest_v683_control_tower_report.html">Control Tower</a></p></section>
"""


def _period_body(period_payload: dict[str, list[dict[str, Any]]]) -> str:
    body = ""
    for route, rows in period_payload.items():
        body += f"<section><h2>{_esc(route)}</h2>{_table(rows, ['period','trade_count','start_equity_krw','end_equity_krw','pnl_krw','return_pct','mdd_pct'])}</section>"
    return body


def _card(label: str, value: Any) -> str:
    return f"<div class='card'><div>{_esc(label)}</div><div class='kpi'>{_esc(value)}</div></div>"


def _table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return "<p class='muted'>No data</p>"
    head = "".join(f"<th>{_esc(key)}</th>" for key in keys)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{_display(row.get(key), key)}</td>" for key in keys) + "</tr>"
    return f"<div class='wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _display(value: Any, key: str) -> str:
    if value is None:
        return "N/A"
    if key.endswith("_krw") or key in {"equity", "today_pnl", "weekly_pnl", "monthly_pnl", "saved_loss_krw", "missed_profit_krw", "net_effect_krw"}:
        return _money(value)
    if key.endswith("_pct") or key in {"return_pct", "mdd_pct", "win_rate_pct", "active_route_return_pct", "best_shadow_return_pct", "delta_pct"}:
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
