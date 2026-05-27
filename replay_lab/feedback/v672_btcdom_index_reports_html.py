from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class V672BTCDOMIndexDataQualityHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v672_btcdom_index_data_quality_summary.json")
        path = self.reports_dir / "latest_v672_btcdom_index_data_quality_report.html"
        path.write_text(_html("V6.7.2 BTCDOM Index 데이터 품질", _quality_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V672BTCDOMIndexScenarioHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v672_btcdom_index_scenario_summary.json")
        path = self.reports_dir / "latest_v672_btcdom_index_scenario_report.html"
        path.write_text(_html("V6.7.2 BTCDOM Index 시나리오 검증", _scenario_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V672BTCDOMIndexSavedLossHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v672_btcdom_index_saved_loss_summary.json")
        path = self.reports_dir / "latest_v672_btcdom_index_saved_loss_report.html"
        path.write_text(_html("V6.7.2 막은 손실 / 놓친 수익", _saved_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V672BTCDOMIndexYearlyHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v672_btcdom_index_yearly_summary.json")
        path = self.reports_dir / "latest_v672_btcdom_index_yearly_report.html"
        path.write_text(_html("V6.7.2 연도별 비교", _yearly_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V672BTCDOMIndexRejectedHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v672_btcdom_index_rejected_scenarios_summary.json")
        path = self.reports_dir / "latest_v672_btcdom_index_rejected_scenarios_report.html"
        path.write_text(_html("V6.7.2 폐기/유지 시나리오", _rejected_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V672BTCDOMIndexCompactRouterHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v672_btcdom_index_compact_router_summary.json")
        path = self.reports_dir / "latest_v672_btcdom_index_compact_router_report.html"
        path.write_text(_html("V6.7.2 BTCDOM Index Compact Router", _compact_body(data)), encoding="utf-8")
        return {"html": str(path)}


def _html(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title><style>
body{{margin:0;background:#f7f9fc;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}
header{{background:#0f172a;color:white;padding:30px 22px}}main{{max-width:1200px;margin:auto;padding:24px}}
section{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:16px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left}}th{{background:#eef2ff}}
.notice{{border-left:5px solid #d97706;background:#fffbeb;padding:13px 15px;border-radius:8px;margin-top:16px}}
.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
</style></head><body><header><h1>{_esc(title)}</h1><p>BTCDOM Index는 BTC Dominance %가 아닐 수 있으므로, 이번 검증은 절대값이 아니라 방향성/기울기 기반 프록시 필터 검증입니다.</p></header><main>
<div class="notice"><strong>안전 고정:</strong> 모든 결과는 PAPER 검증입니다. 실제 주문, 주문 테스트, 출금, 자동 설정 적용은 금지입니다.</div>{body}</main></body></html>"""


def _quality_body(data: dict[str, Any]) -> str:
    files = data.get("files", {})
    rows = "".join(
        f"<tr><td>btcdom_{_esc(tf)}.csv</td><td>{_esc(item.get('exists'))}</td><td>{_esc(item.get('rows'))}</td><td>{_esc(item.get('start'))}</td><td>{_esc(item.get('end'))}</td><td>{_num(item.get('close_min'))}</td><td>{_num(item.get('close_max'))}</td><td>{_esc(item.get('source_type'))}</td><td>{_esc(item.get('quality'))}</td></tr>"
        for tf, item in files.items()
    )
    return f"""<section><h2>한눈에 보는 결론</h2>
<p>source_type: <strong>{_esc(data.get('source_type'))}</strong></p>
<p>percentage 여부: <strong>{_esc(data.get('is_percentage'))}</strong></p>
<p>공통 검증 구간: <strong>{_esc(data.get('common_coverage_start'))}</strong> ~ <strong>{_esc(data.get('common_coverage_end'))}</strong></p>
<p>fake_data_generated: <strong>{_esc(data.get('fake_data_generated'))}</strong></p></section>
<section><h2>파일 품질</h2><table><tr><th>File</th><th>Exists</th><th>Rows</th><th>Start</th><th>End</th><th>Close Min</th><th>Close Max</th><th>Source Type</th><th>Quality</th></tr>{rows}</table></section>"""


def _scenario_body(data: dict[str, Any]) -> str:
    quality = data.get("btcdom_index_quality", {})
    return f"""<section><h2>한눈에 보는 결론</h2><p>{_esc(data.get('reason'))}</p><p>검증 구간은 BTCDOM CSV 공통 coverage 기준입니다: {_esc(quality.get('common_coverage_start'))} ~ {_esc(quality.get('common_coverage_end'))}</p></section>
<section><h2>시나리오 비교</h2>{_scenario_table(data.get('scenarios', []))}</section>
<section><h2>Lookahead / Hindsight 감사</h2>{_audit_table(data.get('audit', {}))}</section>"""


def _saved_body(data: dict[str, Any]) -> str:
    return f"<section><h2>Saved Loss / Missed Profit</h2>{_saved_table(data.get('saved_loss_missed_profit', []))}</section>"


def _yearly_body(data: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td>{_esc(r.get('year'))}</td><td>{_pct(r.get('control_return_pct'))}</td><td>{_esc(r.get('best_btcdom_scenario'))}</td><td>{_pct(r.get('best_btcdom_return_pct'))}</td><td>{_pct(r.get('delta_pct_point'))}p</td><td>{_esc(r.get('notes'))}</td></tr>" for r in data.get("yearly_comparison", []))
    return f"<section><h2>연도별 비교</h2><table><tr><th>Year</th><th>Control</th><th>Best Scenario</th><th>BTCDOM Return</th><th>Delta</th><th>Notes</th></tr>{rows}</table></section>"


def _rejected_body(data: dict[str, Any]) -> str:
    rejected = "".join(f"<tr><td>{_esc(r.get('scenario'))}</td><td>{_esc(r.get('reject_reason'))}</td></tr>" for r in data.get("rejected_scenarios", []))
    kept = "".join(f"<tr><td>{_esc(r.get('scenario'))}</td><td>{_esc(r.get('keep_reason'))}</td><td>{_esc(r.get('forward_candidate'))}</td></tr>" for r in data.get("kept_candidates", []))
    return f"<section><h2>폐기 시나리오</h2><table><tr><th>Scenario</th><th>Reason</th></tr>{rejected}</table></section><section><h2>유지 후보</h2><table><tr><th>Scenario</th><th>Reason</th><th>Forward</th></tr>{kept}</table></section>"


def _compact_body(data: dict[str, Any]) -> str:
    return f"<section><h2>Compact Router</h2>{_scenario_table([data.get('scenario', {})])}</section><section><h2>Net Effect</h2>{_saved_table([data.get('saved_loss_missed_profit', {})])}</section>"


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(f"<tr><td>{_esc(r.get('scenario'))}</td><td>{_money(r.get('final_equity_krw'))}</td><td>{_pct(r.get('total_return_pct'))}</td><td>{_pct(r.get('mdd_pct'))}</td><td>{_num(r.get('profit_factor'))}</td><td>{_esc(r.get('trade_count'))}</td><td>{_num(r.get('return_mdd_ratio'))}</td><td>{_esc(r.get('decision'))}</td></tr>" for r in rows)
    return f"<table><tr><th>Scenario</th><th>Final Equity</th><th>Return</th><th>MDD</th><th>PF</th><th>Trades</th><th>Return/MDD</th><th>Decision</th></tr>{body}</table>"


def _saved_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(f"<tr><td>{_esc(r.get('scenario'))}</td><td>{_money(r.get('saved_loss_krw'))}</td><td>{_money(r.get('missed_profit_krw'))}</td><td>{_money(r.get('net_effect_krw'))}</td><td>{_esc(r.get('decision'))}</td></tr>" for r in rows if r)
    return f"<table><tr><th>Scenario</th><th>Saved Loss</th><th>Missed Profit</th><th>Net Effect</th><th>Decision</th></tr>{body}</table>"


def _audit_table(audit: dict[str, Any]) -> str:
    return f"<table><tr><th>checked</th><th>pass</th><th>fail</th><th>excluded</th><th>major</th></tr><tr><td>{_esc(audit.get('checked_trades'))}</td><td>{_esc(audit.get('pass'))}</td><td>{_esc(audit.get('fail'))}</td><td>{_esc(audit.get('excluded_trades'))}</td><td>{_esc(', '.join(audit.get('major_violations', [])))}</td></tr></table>"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


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
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "N/A"


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
