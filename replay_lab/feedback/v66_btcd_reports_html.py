from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class V66BTCDInclusionAuditHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_inclusion_audit_summary.json")
        path = self.reports_dir / "latest_v66_btcd_inclusion_audit_report.html"
        path.write_text(_simple_html("V6.6 BTC Dominance 포함 여부 감사", _inclusion_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCDDataQualityHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_data_quality_summary.json")
        path = self.reports_dir / "latest_v66_btcd_data_quality_report.html"
        path.write_text(_simple_html("V6.6 BTC Dominance 데이터 품질", _quality_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCDRollingBalancedHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_rolling_balanced_summary.json")
        path = self.reports_dir / "latest_v66_btcd_rolling_balanced_report.html"
        path.write_text(_simple_html("V6.6 Rolling/Balanced + BTC Dominance", _scenario_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCDBearScenarioHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_bear_scenario_summary.json")
        path = self.reports_dir / "latest_v66_btcd_bear_scenario_report.html"
        path.write_text(_simple_html("V6.6 Bear Regime + BTC Dominance", _scenario_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCD202411FocusHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_2024_11_focus_summary.json")
        path = self.reports_dir / "latest_v66_btcd_2024_11_focus_report.html"
        path.write_text(_simple_html("V6.6 2024년 11월 이후 약세장 집중 분석", _focus_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCDSavedLossMissedProfitHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_saved_loss_missed_profit_summary.json")
        path = self.reports_dir / "latest_v66_btcd_saved_loss_missed_profit_report.html"
        path.write_text(_simple_html("V6.6 막은 손실 / 놓친 수익", _saved_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCDShortResearchHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_short_research_summary.json")
        path = self.reports_dir / "latest_v66_btcd_short_research_report.html"
        path.write_text(_simple_html("V6.6 Short/Hedge PAPER 연구", _short_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCDScenarioComparisonHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_scenario_comparison_summary.json")
        path = self.reports_dir / "latest_v66_btcd_scenario_comparison_report.html"
        path.write_text(_simple_html("V6.6 BTC Dominance 시나리오 종합 비교", _scenario_body(summary)), encoding="utf-8")
        return {"html": str(path)}


class V66BTCDHybridRouterHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v66_btcd_hybrid_router_summary.json")
        path = self.reports_dir / "latest_v66_btcd_hybrid_router_report.html"
        path.write_text(_simple_html("V6.6 Hybrid Bear Router + BTC Dominance", _hybrid_body(summary)), encoding="utf-8")
        return {"html": str(path)}


def _simple_html(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <style>
    body{{margin:0;background:#f7f9fc;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}
    header{{background:#0f172a;color:white;padding:30px 22px}}main{{max-width:1240px;margin:auto;padding:24px}}
    section,.card{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:16px}}
    table{{width:100%;border-collapse:collapse;background:white;font-size:14px}}th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left;vertical-align:top}}th{{background:#eef2ff}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
    .kpi{{font-size:25px;font-weight:800;margin-top:4px}}.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
    .notice{{border-left:5px solid #d97706;background:#fffbeb;padding:13px 15px;border-radius:8px;margin-top:16px}}
    .chart{{width:100%;height:auto;border:1px solid #e2e8f0;background:#fff;border-radius:8px}}
  </style>
</head>
<body>
<header>
  <h1>{_esc(title)}</h1>
  <p>BTC Dominance는 매수 신호가 아니라, 알트 시장이 위험해지는지 확인하는 별도 overlay입니다. 기존 Rolling/Balanced 기준선은 수정하지 않았습니다.</p>
</header>
<main>
  <div class="notice"><strong>안전 고정:</strong> 모든 결과는 PAPER 모의투자입니다. 실제 주문, 주문 테스트, 취소, 출금은 사용하지 않았고 real_order_enabled=false, live_order_allowed=false입니다.</div>
  {body}
</main>
</body>
</html>"""


def _inclusion_body(summary: dict[str, Any]) -> str:
    rows = [
        ("Rolling Edge", summary.get("btcd_in_existing_rolling_edge")),
        ("Balanced Growth", summary.get("btcd_in_existing_balanced_growth")),
        ("Policy Blend", summary.get("btcd_in_policy_blend")),
        ("True Walk-Forward", summary.get("btcd_in_true_walk_forward")),
        ("V6.4 Defense", summary.get("btcd_in_v64_defense")),
        ("V6.5 MA Scenario", summary.get("btcd_in_v65_ma")),
    ]
    table = "".join(f"<tr><td>{_esc(name)}</td><td>{'포함' if value else '미포함'}</td></tr>" for name, value in rows)
    evidence = "".join(f"<li>{_esc(item)}</li>" for item in summary.get("evidence", [])) or "<li>직접 포함 증거 없음</li>"
    return f"<section><h2>한눈에 보는 결론</h2><p>{_esc(summary.get('conclusion'))}</p></section><section><table><tr><th>기존 시나리오</th><th>BTC Dominance 포함 여부</th></tr>{table}</table></section><section><h2>증거</h2><ul>{evidence}</ul></section>"


def _quality_body(summary: dict[str, Any]) -> str:
    dq = summary.get("data_quality", {})
    rows = "".join(
        f"<tr><td>{_esc(name)}</td><td>{_esc(item.get('available'))}</td><td>{_esc(item.get('period'))}</td><td>{_esc(item.get('coverage'))}</td><td>{_esc(item.get('notes'))}</td></tr>"
        for name, item in dq.items()
    )
    return f"<section><h2>Global BTC Dominance와 Upbit Proxy 구분</h2><p>Global BTC Dominance는 전체 코인 시장에서 BTC 시총 비중입니다. Upbit BTC Flow Dominance Proxy는 업비트 KRW 시장 안에서 BTC 거래대금이 차지하는 비율입니다. 둘은 다릅니다.</p></section><section><table><tr><th>Data Source</th><th>Available</th><th>Period</th><th>Coverage</th><th>Notes</th></tr>{rows}</table></section>"


def _scenario_body(summary: dict[str, Any]) -> str:
    return f"""
  <section><h2>시나리오 비교</h2>{_scenario_table(summary.get('scenarios', []))}</section>
  <section><h2>막은 손실 / 놓친 수익</h2>{_saved_table(summary.get('saved_loss_missed_profit', []))}</section>
  <section><h2>연도별 결과</h2>{_yearly_table(summary.get('yearly_comparison', []))}</section>
  <section><h2>Lookahead / Hindsight 감사</h2>{_audit_table(summary.get('audit', {}))}</section>
"""


def _focus_body(summary: dict[str, Any]) -> str:
    return f"<section><h2>2024-11 이후 Bear Focus</h2>{_scenario_table(summary.get('bear_focus_period', []))}</section>"


def _saved_body(summary: dict[str, Any]) -> str:
    return f"<section><h2>Saved Loss / Missed Profit / Net Effect</h2>{_saved_table(summary.get('saved_loss_missed_profit', []))}</section>"


def _short_body(summary: dict[str, Any]) -> str:
    research = summary.get("short_research", {})
    return f"<section><h2>Short/Hedge 연구 결론</h2><p>이 결과는 실전 후보가 아니라 PAPER 연구 전용입니다.</p><table><tr><th>항목</th><th>값</th></tr><tr><td>수익률</td><td>{_pct(research.get('short_research_return_pct'))}</td></tr><tr><td>MDD</td><td>{_pct(research.get('short_research_mdd_pct'))}</td></tr><tr><td>판정</td><td>{_esc(research.get('decision'))}</td></tr></table></section>"


def _hybrid_body(summary: dict[str, Any]) -> str:
    return f"<section><h2>Hybrid Bear Router</h2>{_scenario_table([summary.get('scenario', {})])}</section><section><h2>Net Effect</h2>{_saved_table([summary.get('saved_loss_missed_profit', {})])}</section><section><h2>감사</h2>{_audit_table(summary.get('audit', {}))}</section>"


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_esc(row.get('scenario'))}</td><td>{_money(row.get('final_equity_krw'))}</td><td>{_pct(row.get('total_return_pct'))}</td><td>{_pct(row.get('mdd_pct'))}</td><td>{_num(row.get('profit_factor'))}</td><td>{int(row.get('trade_count', 0) or 0)}</td><td>{_num(row.get('return_mdd_ratio'))}</td><td>{_esc(row.get('decision'))}</td></tr>"
        for row in rows
    )
    return "<table><tr><th>Scenario</th><th>최종 평가금</th><th>수익률</th><th>최대 낙폭(MDD)</th><th>손익비 계수(PF)</th><th>거래 수</th><th>Return/MDD</th><th>판정</th></tr>" + body + "</table>"


def _saved_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_esc(row.get('scenario'))}</td><td>{_money(row.get('saved_loss_krw'))}</td><td>{_money(row.get('missed_profit_krw'))}</td><td>{_money(row.get('net_effect_krw'))}</td><td>{_esc(row.get('decision'))}</td></tr>"
        for row in rows if row
    )
    return "<table><tr><th>Scenario</th><th>막은 손실</th><th>놓친 수익</th><th>순효과</th><th>판정</th></tr>" + body + "</table>"


def _yearly_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_esc(row.get('year'))}</td><td>{_pct(row.get('control_return_pct'))}</td><td>{_esc(row.get('best_btcd_scenario'))}</td><td>{_pct(row.get('best_btcd_return_pct'))}</td><td>{_pct(row.get('delta_pct_point'))}p</td><td>{_esc(row.get('notes'))}</td></tr>"
        for row in rows
    )
    return "<table><tr><th>Year</th><th>Control</th><th>Best BTCD Scenario</th><th>BTCD Return</th><th>Delta</th><th>Notes</th></tr>" + body + "</table>"


def _audit_table(audit: dict[str, Any]) -> str:
    return f"<table><tr><th>checked_trades</th><th>pass</th><th>fail</th><th>excluded</th><th>major violations</th></tr><tr><td>{int(audit.get('checked_trades', 0) or 0)}</td><td>{int(audit.get('pass', 0) or 0)}</td><td>{int(audit.get('fail', 0) or 0)}</td><td>{int(audit.get('excluded_trades', 0) or 0)}</td><td>{_esc(', '.join(audit.get('major_violations', [])))}</td></tr></table>"


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
