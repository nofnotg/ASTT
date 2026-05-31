from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


class V686ReportsHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.root = Path(reports_dir)

    def build_atr_ltf_coverage(self) -> dict[str, str]:
        return self._build("latest_v686_atr_ltf_coverage_summary.json", "latest_v686_atr_ltf_coverage_report.html", "V6.8.6 ATR LTF Coverage", _coverage_body)

    def build_atr_ltf_replay(self) -> dict[str, str]:
        return self._build("latest_v686_atr_ltf_replay_summary.json", "latest_v686_atr_ltf_replay_report.html", "V6.8.6 ATR LTF Replay", _ltf_replay_body)

    def build_atr_precision_v2(self) -> dict[str, str]:
        return self._build("latest_v686_atr_precision_v2_summary.json", "latest_v686_atr_precision_v2_report.html", "V6.8.6 ATR Precision V2", _precision_body)

    def build_atr_model_comparison(self) -> dict[str, str]:
        return self._build("latest_v686_atr_model_comparison_summary.json", "latest_v686_atr_model_comparison_report.html", "V6.8.6 ATR Model Comparison", _model_body)

    def build_bear_window_atr_replay(self) -> dict[str, str]:
        return self._build("latest_v686_bear_window_atr_replay_summary.json", "latest_v686_bear_window_atr_replay_report.html", "V6.8.6 Bear Window ATR Replay", _bear_atr_body)

    def build_active_shadow_runtime(self) -> dict[str, str]:
        return self._build("latest_v686_active_shadow_runtime_summary.json", "latest_v686_active_shadow_runtime_report.html", "V6.8.6 Active Shadow Runtime", _runtime_body)

    def build_local_dashboard(self) -> dict[str, str]:
        return self._build("latest_v686_local_dashboard_summary.json", "latest_v686_local_dashboard_report.html", "V6.8.6 Local Dashboard", _dashboard_body)

    def build_control_tower_dashboard(self) -> dict[str, str]:
        return self._build("latest_v686_control_tower_dashboard_summary.json", "latest_v686_control_tower_dashboard_report.html", "V6.8.6 Control Tower Dashboard Review", _control_body)

    def build_dashboard(self) -> dict[str, str]:
        path = self.root / "astt_report_dashboard.html"
        existing = path.read_text(encoding="utf-8-sig") if path.exists() else _layout("ASTT Report Dashboard", "")
        block = _dashboard_block()
        if "V6.8.6 ATR LTF Replay + Local Dashboard" not in existing:
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
<style>body{{margin:0;background:#f7f8fb;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.6}}header{{background:#101828;color:white;padding:28px 22px}}main{{max-width:1280px;margin:auto;padding:22px}}section{{background:white;border:1px solid #d8dee8;border-radius:8px;padding:16px;margin:14px 0}}.notice{{border-left:5px solid #b42318;background:#fff7f5}}.ok{{border-left-color:#067647;background:#f6fef9}}.wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#f2f4f7}}a{{color:#1d4ed8}}</style></head><body><header><h1>{_esc(title)}</h1><p>Paper/research only. Live orders disabled.</p></header><main>{body}</main></body></html>"""


def _coverage_body(p: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>Decision</h2><p>{_esc(p.get('decision'))} / fake_data_generated={_esc(p.get('fake_data_generated'))}</p></section><section>{_table([p], ['total_atr_trades','covered_by_1m','covered_by_5m','covered_by_15m','uncovered','coverage_pct_1m','coverage_pct_5m','coverage_pct_15m','best_coverage_pct','decision'])}</section><section>{_table([p.get('backfill_plan', {})], ['missing_trade_count','markets_to_backfill','next_action'])}</section>"


def _ltf_replay_body(p: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>ATR LTF Replay</h2><p>{_esc(p.get('final_atr_decision'))}</p></section><section>{_table(p.get('model_rows', []), ['scenario','fill_model','final_equity_krw','return_pct','mdd_pct','profit_factor','ltf_coverage_pct','decision'])}</section><section>{_table(p.get('sample_rows', [])[:50], ['trade_id','market','fill_model','ltf_available','bar_count','decision'])}</section>"


def _precision_body(p: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>Final ATR Decision</h2><p>{_esc(p.get('final_atr_decision'))}: {_esc(p.get('reason'))}</p></section><section>{_table(p.get('rows', [])[:120], ['scenario','fill_model','atr_period','atr_multiplier','atr_timeframe','trailing_update_mode','return_pct','mdd_pct','ltf_coverage_pct','conflict_pct','decision'])}</section>"


def _model_body(p: dict[str, Any]) -> str:
    return f"<section><h2>Model Comparison</h2>{_table(p.get('rows', []), ['scenario','fill_model','final_equity_krw','return_pct','mdd_pct','profit_factor','ltf_coverage_pct','decision'])}</section>"


def _bear_atr_body(p: dict[str, Any]) -> str:
    return f"<section class='notice'><h2>ATR In Bear Windows</h2><p>{_esc(p.get('atr_final_decision'))}</p></section><section>{_table(p.get('rows', []), ['window','type','active_return','best_non_atr_route','best_non_atr_return','best_atr_route','best_atr_return','atr_decision','recommended_action'])}</section>"


def _runtime_body(p: dict[str, Any]) -> str:
    return f"<section class='ok'><h2>Runtime</h2><p>active={_esc(p.get('active_route'))} / active_change_applied={_esc(p.get('active_route_change_applied'))}</p></section><section>{_table(p.get('routes', []), ['scenario','route_status','final_equity_krw','return_pct','mdd_pct','decision'])}</section>"


def _dashboard_body(p: dict[str, Any]) -> str:
    return f"<section class='ok'><h2>Local Dashboard</h2><p><a href='{_esc(p.get('browser_url'))}'>{_esc(p.get('browser_url'))}</a></p></section><section>{_table([p], ['dashboard_ready','host','port','paper_runtime_connected','llm_review_enabled','live_order_endpoints_enabled','real_order_enabled','live_order_allowed','decision'])}</section>"


def _control_body(p: dict[str, Any]) -> str:
    return f"<section><h2>Recommendations</h2>{_table([{'recommendation': item} for item in p.get('recommendations', [])], ['recommendation'])}</section><section>{_table([{'risk_flag': item} for item in p.get('risk_flags', [])], ['risk_flag'])}</section>"


def _dashboard_block() -> str:
    links = [
        ("ATR LTF Coverage", "latest_v686_atr_ltf_coverage_report.html"),
        ("ATR LTF Replay", "latest_v686_atr_ltf_replay_report.html"),
        ("ATR Precision V2", "latest_v686_atr_precision_v2_report.html"),
        ("ATR Model Comparison", "latest_v686_atr_model_comparison_report.html"),
        ("Bear Window ATR Replay", "latest_v686_bear_window_atr_replay_report.html"),
        ("Active Shadow Runtime", "latest_v686_active_shadow_runtime_report.html"),
        ("Local Dashboard", "latest_v686_local_dashboard_report.html"),
        ("Control Tower", "latest_v686_control_tower_dashboard_report.html"),
    ]
    body = " / ".join(f"<a href='{href}'>{_esc(label)}</a>" for label, href in links)
    return f"<section><h2>V6.8.6 ATR LTF Replay + Local Dashboard</h2><p>{body}</p></section>"


def _table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return "<p>No data</p>"
    head = "".join(f"<th>{_esc(key)}</th>" for key in keys)
    body = "".join("<tr>" + "".join(f"<td>{_display(row.get(key), key)}</td>" for key in keys) + "</tr>" for row in rows)
    return f"<div class='wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _display(value: Any, key: str) -> str:
    if isinstance(value, list):
        return _esc(", ".join(str(item) for item in value[:12]))
    if value is None:
        return "N/A"
    if key.endswith("_krw") or "equity" in key:
        return f"{float(value):,.0f} KRW" if _is_num(value) else _esc(value)
    if key.endswith("_pct") or "return" in key or "mdd" in key or "coverage" in key:
        return f"{float(value):+.2f}%" if _is_num(value) else _esc(value)
    return _esc(value)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)


def _is_num(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
