from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class V65MAScenarioReportHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v65_ma_scenario_summary.json")
        path = self.reports_dir / "latest_v65_ma_scenario_report.html"
        path.write_text(_html("ASTT V6.5 MA 시나리오 비교", summary, "scenario"), encoding="utf-8")
        return {"html": str(path)}


class V65MAPolicyRouterReportHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v65_ma_policy_router_summary.json")
        scenario = _read(self.reports_dir / "latest_v65_ma_scenario_summary.json")
        path = self.reports_dir / "latest_v65_ma_policy_router_report.html"
        path.write_text(_html("ASTT V6.5 MA 정책 라우터 검증", {**scenario, "router_focus": summary}, "router"), encoding="utf-8")
        return {"html": str(path)}


class V65YearlyRepairReportHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v65_yearly_repair_summary.json")
        scenario = _read(self.reports_dir / "latest_v65_ma_scenario_summary.json")
        path = self.reports_dir / "latest_v65_yearly_repair_report.html"
        path.write_text(_html("ASTT V6.5 2025/2026 약점 보완 분석", {**scenario, "repair_focus": summary}, "repair"), encoding="utf-8")
        return {"html": str(path)}


class V65MARiskReportHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_v65_ma_risk_summary.json")
        scenario = _read(self.reports_dir / "latest_v65_ma_scenario_summary.json")
        path = self.reports_dir / "latest_v65_ma_risk_report.html"
        path.write_text(_html("ASTT V6.5 MA 리스크 리포트", {**scenario, "risk_focus": summary}, "risk"), encoding="utf-8")
        return {"html": str(path)}


def _html(title: str, summary: dict[str, Any], mode: str) -> str:
    scenarios = summary.get("scenarios") or summary.get("scenario_rows", [])
    rec = summary.get("recommendation", {})
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body{{margin:0;background:#f7f9fc;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.62}}
    header{{background:#111827;color:white;padding:30px 22px}}main{{max-width:1240px;margin:auto;padding:24px}}
    section,.card{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:16px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
    .kpi{{font-size:25px;font-weight:800;margin-top:4px}}.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
    table{{width:100%;border-collapse:collapse;background:white;font-size:14px}}th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left;vertical-align:top}}th{{background:#eef2ff}}
    .notice{{border-left:5px solid #d97706;background:#fffbeb;padding:13px 15px;border-radius:8px;margin-top:16px}}
    .chart{{width:100%;height:auto;border:1px solid #e2e8f0;background:#fff;border-radius:8px}}
  </style>
</head>
<body>
<header>
  <h1>{html.escape(title)}</h1>
  <p>DaddyBTC 20/200 SMA와 Testa 5/25/75 MA를 단독 매수 신호가 아니라 기존 ICT/Combined 전략의 필터와 정책 라우터 입력으로 검증했습니다.</p>
</header>
<main>
  <div class="notice"><strong>안전 고정:</strong> 모든 결과는 PAPER 모의투자입니다. 실제 주문, 주문 테스트, 취소, 출금은 사용하지 않았고 real_order_enabled=false, live_order_allowed=false입니다.</div>
  <section>
    <h2>한눈에 보는 결론</h2>
    <div class="grid">
      <div class="card"><div>추천 시나리오</div><div class="kpi">{html.escape(str(rec.get('best_scenario', '분석 필요')))}</div></div>
      <div class="card"><div>최종 판단</div><div class="kpi">{html.escape(str(rec.get('final_judgement', 'LIVE_NOT_ALLOWED')))}</div></div>
      <div class="card"><div>Lookahead 실패</div><div class="kpi">{int(summary.get('audit', {}).get('fail', 0))}</div></div>
      <div class="card"><div>폐기할 필터</div><div class="kpi bad">MA Hard Filter</div></div>
    </div>
    <p>결론은 단호합니다. MA_CHOP, MA_BEAR, TESTA_LOST_75 같은 hard no-trade 필터는 폐기합니다. MDD는 줄였지만 2023/2024의 큰 수익을 과도하게 잘라먹었고, 2025/2026 약한 해도 개선하지 못했습니다.</p>
    <p>MA는 매수 버튼이 아닙니다. 이번 검증의 질문은 “MA가 쉬어야 할 장, 줄여야 할 장, 기존 성공 셋업을 더 믿어도 되는 장을 구분했는가”였고, 현 규칙은 그 기준을 통과하지 못했습니다.</p>
  </section>
  <section><h2>시나리오별 성과 비교</h2>{_scenario_table(scenarios)}</section>
  <section><h2>연도별 수익률 비교</h2>{_yearly_table(summary.get('yearly_comparison', []))}{_yearly_chart(summary.get('yearly_comparison', []))}</section>
  <section><h2>2025/2026 약한 해 보완 여부</h2>{_weak_table(summary.get('weak_year_repair', {}))}</section>
  <section><h2>Plan별 영향</h2>{_impact_table(summary.get('plan_impact', []), 'plan')}</section>
  <section><h2>MA 조건별 효과</h2>{_attribution_table(summary.get('ma_condition_attribution', []))}{_condition_table(summary.get('ma_condition_effect', []))}</section>
  <section><h2>Equity Curve 비교</h2>{_line_chart(summary.get('equity_curve', {}), 'equity')}</section>
  <section><h2>Drawdown Curve 비교</h2>{_line_chart(summary.get('drawdown_curve', {}), 'drawdown_pct')}</section>
  <section><h2>Lookahead / Hindsight Audit</h2>{_audit_table(summary.get('audit', {}))}</section>
  <section>
    <h2>실전 금지 사유</h2>
    <p>V6.5가 통과해도 아직 OHLCV 기반 검증입니다. 실제 spread/depth/slippage overlay와 forward paper 검증이 끝나기 전까지 LIVE 전환은 금지입니다.</p>
  </section>
</main>
</body>
</html>"""


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_esc(row.get('scenario'))}</td><td>{_money(row.get('final_equity_krw'))}</td><td>{_pct(row.get('total_return_pct'))}</td><td>{_pct(row.get('mdd_pct'))}</td><td>{_num(row.get('profit_factor'))}</td><td>{int(row.get('trade_count', 0))}</td><td>{int(row.get('skipped_trade_count', 0))}</td><td>{_num(row.get('return_mdd_ratio'))}</td><td>{_esc(row.get('decision'))}</td></tr>"
        for row in rows
    )
    return "<table><tr><th>Scenario</th><th>최종 평가금</th><th>수익률</th><th>MDD</th><th>PF</th><th>거래</th><th>스킵</th><th>Return/MDD</th><th>판정</th></tr>" + body + "</table>"


def _yearly_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{row.get('year')}</td><td>{_pct(row.get('control_return_pct'))}</td><td>{_pct(row.get('MA_POLICY_ROUTER_return_pct'))}</td><td>{_pct(row.get('MA_POLICY_ROUTER_delta_pct_point'))}p</td><td>{_pct(row.get('MA_DEFENSIVE_REPAIR_return_pct'))}</td><td>{_pct(row.get('MA_DEFENSIVE_REPAIR_delta_pct_point'))}p</td></tr>"
        for row in rows
    )
    return "<table><tr><th>연도</th><th>Control</th><th>MA Router</th><th>Router 차이</th><th>Defensive Repair</th><th>Repair 차이</th></tr>" + body + "</table>"


def _weak_table(data: dict[str, Any]) -> str:
    body = "".join(
        f"<tr><td>{_esc(name)}</td><td>{_pct(row.get('2025_return_pct'))}</td><td>{int(row.get('2025_trades', 0))}</td><td>{_pct(row.get('2026_return_pct'))}</td><td>{int(row.get('2026_trades', 0))}</td><td>{_money(row.get('defensive_state_pnl'))}</td><td>{_money(row.get('caution_state_pnl'))}</td></tr>"
        for name, row in data.items()
    )
    return "<table><tr><th>시나리오</th><th>2025 수익률</th><th>2025 거래</th><th>2026 수익률</th><th>2026 거래</th><th>DEFENSIVE 손익</th><th>CAUTION 손익</th></tr>" + body + "</table>"


def _impact_table(rows: list[dict[str, Any]], key: str) -> str:
    filtered = [row for row in rows if row.get("scenario") in {"CONTROL_CURRENT_ROUTER", "MA_POLICY_ROUTER", "MA_DEFENSIVE_REPAIR"}]
    body = "".join(
        f"<tr><td>{_esc(row.get('scenario'))}</td><td>{_esc(row.get(key))}</td><td>{_money(row.get('control_pnl_krw'))}</td><td>{_money(row.get('pnl_krw'))}</td><td>{_money(row.get('delta_krw'))}</td><td>{int(row.get('trade_count', 0))}</td></tr>"
        for row in filtered
    )
    return f"<table><tr><th>시나리오</th><th>{key}</th><th>Control PnL</th><th>시나리오 PnL</th><th>차이</th><th>거래</th></tr>{body}</table>"


def _condition_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_esc(row.get('ma_condition'))}</td><td>{_esc(row.get('effect'))}</td><td>{_esc(row.get('decision'))}</td></tr>"
        for row in rows
    )
    return "<table><tr><th>MA 조건</th><th>효과</th><th>유지/폐기</th></tr>" + body + "</table>"


def _attribution_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_esc(row.get('ma_condition'))}</td><td>{int(row.get('trigger_count', 0))}</td><td>{int(row.get('blocked_trades', 0))}</td><td>{_money(row.get('saved_loss_krw'))}</td><td>{_money(row.get('missed_profit_krw'))}</td><td>{_money(row.get('net_effect_krw'))}</td><td>{_esc(row.get('decision'))}</td></tr>"
        for row in rows
    )
    return "<table><tr><th>MA Condition</th><th>Trigger Count</th><th>Blocked Trades</th><th>Saved Loss</th><th>Missed Profit</th><th>Net Effect</th><th>Decision</th></tr>" + body + "</table>"


def _audit_table(audit: dict[str, Any]) -> str:
    return f"<table><tr><th>checked_trades</th><th>pass</th><th>fail</th><th>excluded</th><th>major violations</th></tr><tr><td>{int(audit.get('checked_trades', 0))}</td><td>{int(audit.get('pass', 0))}</td><td>{int(audit.get('fail', 0))}</td><td>{int(audit.get('excluded_trades', 0))}</td><td>{_esc(', '.join(audit.get('major_violations', [])))}</td></tr></table>"


def _yearly_chart(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    keys = [str(row["year"]) for row in rows]
    control = [float(row.get("control_return_pct", 0.0)) for row in rows]
    router = [float(row.get("MA_POLICY_ROUTER_return_pct", 0.0)) for row in rows]
    return _bar_chart(keys, [("Control", control, "#64748b"), ("MA Router", router, "#16a34a")], "연도별 수익률")


def _bar_chart(labels: list[str], series: list[tuple[str, list[float], str]], title: str) -> str:
    width, height, pad = 980, 300, 42
    values = [v for _, vals, _ in series for v in vals]
    max_abs = max([abs(v) for v in values] + [1.0])
    zero = height / 2
    group = (width - pad * 2) / max(1, len(labels))
    bar_w = min(20, group / (len(series) + 1))
    parts = []
    for i, _label in enumerate(labels):
        center = pad + i * group + group / 2
        for sidx, (_name, vals, color) in enumerate(series):
            val = vals[i]
            h = abs(val) / max_abs * (height / 2 - pad)
            y = zero - h if val >= 0 else zero
            x = center + (sidx - (len(series) - 1) / 2) * bar_w - bar_w / 2
            parts.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bar_w:.1f}' height='{h:.1f}' fill='{color}'/>")
        parts.append(f"<text x='{center:.1f}' y='{height-8}' font-size='11' text-anchor='middle'>{_esc(_label)}</text>")
    legend = " ".join(f"<span style='color:{color};font-weight:700'>{name}</span>" for name, _, color in series)
    return f"<div>{legend}</div><svg class='chart' viewBox='0 0 {width} {height}' aria-label='{_esc(title)}'><line x1='{pad}' y1='{zero}' x2='{width-pad}' y2='{zero}' stroke='#94a3b8'/>{''.join(parts)}</svg>"


def _line_chart(curves: dict[str, list[dict[str, Any]]], key: str) -> str:
    selected = {name: rows for name, rows in curves.items() if name in {"CONTROL_CURRENT_ROUTER", "MA_POLICY_ROUTER", "MA_DEFENSIVE_REPAIR"} and rows}
    vals = [float(row.get(key, 0.0)) for rows in selected.values() for row in rows]
    if not vals:
        return "<p>차트 데이터가 없습니다.</p>"
    width, height, pad = 980, 310, 40
    mn, mx = min(vals), max(vals)
    if mn == mx:
        mx += 1
    colors = {"CONTROL_CURRENT_ROUTER": "#64748b", "MA_POLICY_ROUTER": "#16a34a", "MA_DEFENSIVE_REPAIR": "#2563eb"}
    lines = []
    legend = []
    for name, rows in selected.items():
        points = []
        for idx, row in enumerate(rows):
            x = pad + idx / max(1, len(rows) - 1) * (width - pad * 2)
            y = height - pad - ((float(row.get(key, 0.0)) - mn) / (mx - mn) * (height - pad * 2))
            points.append(f"{x:.1f},{y:.1f}")
        color = colors.get(name, "#111827")
        lines.append(f"<polyline fill='none' stroke='{color}' stroke-width='2.7' points='{' '.join(points)}'/>")
        legend.append(f"<span style='color:{color};font-weight:700'>{name}</span>")
    return f"<div>{' '.join(legend)}</div><svg class='chart' viewBox='0 0 {width} {height}'><line x1='{pad}' y1='{height-pad}' x2='{width-pad}' y2='{height-pad}' stroke='#cbd5e1'/>{''.join(lines)}</svg>"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return html.escape(str(value or ""))


def _money(value: Any) -> str:
    return f"{float(value or 0.0):,.0f}원"


def _pct(value: Any) -> str:
    return f"{float(value or 0.0):+.2f}%"


def _num(value: Any) -> str:
    return f"{float(value or 0.0):.2f}"
