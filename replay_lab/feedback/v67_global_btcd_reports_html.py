from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class V67GlobalBTCDDataQualityHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v67_global_btcd_data_quality_summary.json")
        path = self.reports_dir / "latest_v67_global_btcd_data_quality_report.html"
        path.write_text(_html("V6.7 Global BTC Dominance 데이터 품질", _quality_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V67GlobalBTCDScenarioHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v67_global_btcd_scenario_summary.json")
        path = self.reports_dir / "latest_v67_global_btcd_scenario_report.html"
        path.write_text(_html("V6.7 Global BTC Dominance 시나리오 검증", _scenario_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V67GlobalBTCDSavedLossHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v67_global_btcd_saved_loss_summary.json")
        path = self.reports_dir / "latest_v67_global_btcd_saved_loss_report.html"
        path.write_text(_html("V6.7 막은 손실 / 놓친 수익", _saved_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V67GlobalBTCDYearlyHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v67_global_btcd_yearly_summary.json")
        path = self.reports_dir / "latest_v67_global_btcd_yearly_report.html"
        path.write_text(_html("V6.7 연도별 Global BTCD 비교", _yearly_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V67GlobalBTCDRejectedHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v67_global_btcd_rejected_scenarios_summary.json")
        path = self.reports_dir / "latest_v67_global_btcd_rejected_scenarios_report.html"
        path.write_text(_html("V6.7 폐기 시나리오", _rejected_body(data)), encoding="utf-8")
        return {"html": str(path)}


class V67GlobalBTCDCompactRouterHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_v67_global_btcd_compact_router_summary.json")
        path = self.reports_dir / "latest_v67_global_btcd_compact_router_report.html"
        path.write_text(_html("V6.7 Global BTCD Compact Router", _compact_body(data)), encoding="utf-8")
        return {"html": str(path)}


def _html(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title><style>
body{{margin:0;background:#f7f9fc;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}
header{{background:#0f172a;color:white;padding:30px 22px}}main{{max-width:1200px;margin:auto;padding:24px}}
section{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:16px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left}}th{{background:#eef2ff}}
.notice{{border-left:5px solid #d97706;background:#fffbeb;padding:13px 15px;border-radius:8px;margin-top:16px}}
.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
</style></head><body><header><h1>{_esc(title)}</h1><p>Global BTC Dominance는 매수 신호가 아니라 알트코인 매매 허용/축소/관찰을 판단하는 시장 체질 필터입니다.</p></header><main>
<div class="notice"><strong>안전 고정:</strong> 모든 결과는 PAPER 검증입니다. 실제 주문, 주문 테스트, 출금, 자동 설정 적용은 금지입니다.</div>{body}</main></body></html>"""


def _quality_body(data: dict[str, Any]) -> str:
    sources = data.get("data_sources", {})
    rows = "".join(f"<tr><td>{_esc(k)}</td><td>{_esc(v.get('available'))}</td><td>{_esc(v.get('period'))}</td><td>{_esc(v.get('coverage'))}</td><td>{_esc(v.get('notes') or v.get('reason'))}</td></tr>" for k, v in sources.items())
    possible = data.get("full_period_validation_possible")
    return f"<section><h2>한눈에 보는 결론</h2><p>2022년부터 Global BTC Dominance 백테스트 가능 여부: <strong>{_esc(possible)}</strong></p><p>{_esc(data.get('reason'))}</p></section><section><h2>데이터 소스</h2><table><tr><th>Source</th><th>Available</th><th>Period</th><th>Coverage</th><th>Notes</th></tr>{rows}</table></section>"


def _scenario_body(data: dict[str, Any]) -> str:
    return f"<section><h2>시나리오 성과 비교</h2>{_scenario_table(data.get('scenarios', []))}</section><section><h2>감사</h2>{_audit_table(data.get('audit', {}))}</section>"


def _saved_body(data: dict[str, Any]) -> str:
    return f"<section><h2>Saved Loss / Missed Profit</h2>{_saved_table(data.get('saved_loss_missed_profit', []))}</section>"


def _yearly_body(data: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td>{_esc(r.get('year'))}</td><td>{_pct(r.get('control_return_pct'))}</td><td>{_esc(r.get('best_global_btcd_scenario'))}</td><td>{_pct(r.get('best_global_btcd_return_pct'))}</td><td>{_pct(r.get('delta_pct_point'))}p</td><td>{_esc(r.get('notes'))}</td></tr>" for r in data.get("yearly_comparison", []))
    return f"<section><h2>연도별 비교</h2><table><tr><th>Year</th><th>Control</th><th>Best Scenario</th><th>BTCD Return</th><th>Delta</th><th>Notes</th></tr>{rows}</table></section>"


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
