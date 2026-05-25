from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v64_policy_compounding_analyzer import analyze_policy_aware_compounding


def build_v64_policy_compounding_analysis(reports_dir: str = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    source = _read(root / "latest_true_walk_forward_summary.json")
    journal = source.get("journal", [])
    initial = float(source.get("capital", {}).get("initial_cash_krw", 500000.0) or 500000.0)
    summary = analyze_policy_aware_compounding(journal, initial)
    _write(root / "latest_v64_policy_compounding_summary.json", summary)
    _write_text(root / "latest_v64_policy_compounding_report.html", _html(summary))
    return summary


def _html(summary: dict[str, Any]) -> str:
    scenarios = summary.get("scenarios", [])
    rolling = next((row for row in scenarios if row.get("scenario") == "ROLLING_EDGE_THROTTLE"), {})
    balanced = next((row for row in scenarios if row.get("scenario") == "BALANCED_GROWTH"), {})
    compare = summary.get("rolling_vs_balanced", {})
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT V6.4 Rolling vs Balanced 복리 재산정</title>
  <style>
    body{{margin:0;background:#f7f9fc;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.6}}
    header{{background:#0f172a;color:white;padding:30px 22px}}main{{max-width:1220px;margin:auto;padding:24px}}
    section,.card{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:16px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
    .kpi{{font-size:25px;font-weight:800;margin-top:4px}}.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
    table{{width:100%;border-collapse:collapse;font-size:14px;background:white}}th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left;vertical-align:top}}th{{background:#eef2ff}}
    .notice{{border-left:5px solid #d97706;background:#fffbeb;padding:13px 15px;border-radius:8px;margin-top:16px}}
    .chart{{width:100%;height:auto;border:1px solid #e2e8f0;background:#fff;border-radius:8px}}
  </style>
</head>
<body>
<header>
  <h1>ASTT V6.4 Rolling vs Balanced 복리 재산정</h1>
  <p>두 정책을 각각 독립 계좌로 두고, 매 거래마다 그 시점의 평가금으로 포지션을 다시 산정한 진짜 복리 비교입니다.</p>
</header>
<main>
  <div class="notice"><strong>안전 고지:</strong> 이 리포트는 PAPER 모의투자입니다. 실제 주문, 주문 테스트, 취소, 출금은 사용하지 않았고 real_order_enabled=false, live_order_allowed=false입니다.</div>
  <section>
    <h2>한눈에 보는 결론</h2>
    <p>기존 V6.4 정책 비교는 기존 거래 손익에 방어 배수를 곱한 재검증이었습니다. 이 리포트는 정책별 평가금을 기준으로 포지션 크기와 손익을 매번 다시 계산했습니다. 따라서 Rolling Edge와 Balanced Growth의 복리 효과 차이를 더 직접적으로 볼 수 있습니다.</p>
    <div class="grid">
      <div class="card"><div>Rolling 최종 평가금</div><div class="kpi good">{_money(rolling.get('final_equity_krw'))}</div></div>
      <div class="card"><div>Balanced 최종 평가금</div><div class="kpi good">{_money(balanced.get('final_equity_krw'))}</div></div>
      <div class="card"><div>Balanced - Rolling</div><div class="kpi {'good' if float(compare.get('balanced_final_equity_delta_krw', 0)) >= 0 else 'bad'}">{_money(compare.get('balanced_final_equity_delta_krw'))}</div></div>
      <div class="card"><div>Rolling MDD</div><div class="kpi warn">{_pct(rolling.get('mdd_pct'))}</div></div>
      <div class="card"><div>Balanced MDD</div><div class="kpi warn">{_pct(balanced.get('mdd_pct'))}</div></div>
      <div class="card"><div>추천 정책</div><div class="kpi">{summary.get('recommendation', {}).get('primary')}</div></div>
    </div>
  </section>
  <section><h2>복리 재산정 시나리오 비교</h2>{_scenario_table(scenarios)}</section>
  <section>
    <h2>계좌 평가금(Equity) 곡선</h2>
    {_line_chart(summary.get('equity_curve', {}), value_key='equity', title='Equity')}
  </section>
  <section>
    <h2>최대 낙폭(MDD) 곡선</h2>
    {_line_chart(summary.get('drawdown_curve', {}), value_key='drawdown_pct', title='Drawdown')}
  </section>
  <section><h2>연별 수익률</h2>{_bar_chart(summary, 'yearly', '연별 수익률')}{_period_compare_table(summary, 'yearly')}</section>
  <section><h2>월별 수익률</h2>{_bar_chart(summary, 'monthly', '월별 수익률')}{_period_compare_table(summary, 'monthly')}</section>
  <section><h2>주별 수익률</h2>{_bar_chart(summary, 'weekly', '최근 주별 수익률', limit=40)}{_period_compare_table(summary, 'weekly', limit=80)}</section>
  <section><h2>플랜별 성과</h2>{_group_tables(summary.get('plan_performance', {}), 'plan')}</section>
  <section><h2>전략별 성과</h2>{_group_tables(summary.get('strategy_performance', {}), 'strategy')}</section>
</main>
</body>
</html>"""


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{row.get('scenario')}</td><td>{_money(row.get('final_equity_krw'))}</td><td>{_pct(row.get('return_pct'))}</td><td>{_pct(row.get('mdd_pct'))}</td><td>{float(row.get('profit_factor', 0.0)):.3f}</td><td>{float(row.get('return_mdd_ratio', 0.0)):.2f}</td><td>{int(row.get('trade_count', 0))}</td><td>{_money(row.get('average_position_krw'))}</td></tr>"
        for row in rows
    )
    return f"<table><tr><th>정책</th><th>최종 평가금</th><th>총수익률</th><th>MDD</th><th>PF</th><th>Return/MDD</th><th>거래수</th><th>평균 포지션</th></tr>{body}</table>"


def _period_compare_table(summary: dict[str, Any], period: str, limit: int | None = None) -> str:
    periods = summary.get("period_returns", {})
    left = {row["period"]: row for row in periods.get("ROLLING_EDGE_THROTTLE", {}).get(period, [])}
    right = {row["period"]: row for row in periods.get("BALANCED_GROWTH", {}).get(period, [])}
    keys = sorted(set(left) | set(right))
    if limit:
        keys = keys[-limit:]
    body = "".join(
        f"<tr><td>{key}</td><td>{_pct(left.get(key, {}).get('return_pct'))}</td><td>{_money(left.get(key, {}).get('end_equity'))}</td><td>{_pct(left.get(key, {}).get('mdd_pct'))}</td><td>{_pct(right.get(key, {}).get('return_pct'))}</td><td>{_money(right.get(key, {}).get('end_equity'))}</td><td>{_pct(right.get(key, {}).get('mdd_pct'))}</td><td>{_pct((right.get(key, {}).get('return_pct') or 0) - (left.get(key, {}).get('return_pct') or 0))}p</td></tr>"
        for key in keys
    )
    return f"<table><tr><th>기간</th><th>Rolling 수익률</th><th>Rolling 평가금</th><th>Rolling MDD</th><th>Balanced 수익률</th><th>Balanced 평가금</th><th>Balanced MDD</th><th>수익률 차이</th></tr>{body}</table>"


def _group_tables(groups: dict[str, list[dict[str, Any]]], key: str) -> str:
    rows = []
    for policy, items in groups.items():
        for row in items:
            rows.append(
                f"<tr><td>{policy}</td><td>{row.get(key)}</td><td>{int(row.get('trade_count', 0))}</td><td>{_money(row.get('pnl_krw'))}</td><td>{_pct(row.get('win_rate_pct'))}</td><td>{float(row.get('profit_factor', 0.0)):.3f}</td></tr>"
            )
    return f"<table><tr><th>정책</th><th>{key}</th><th>거래수</th><th>PnL</th><th>승률</th><th>PF</th></tr>{''.join(rows)}</table>"


def _line_chart(curves: dict[str, list[dict[str, Any]]], value_key: str, title: str) -> str:
    width, height, pad = 1000, 320, 38
    series = {name: rows for name, rows in curves.items() if rows}
    values = [float(row.get(value_key, 0.0)) for rows in series.values() for row in rows]
    if not values:
        return "<p>차트 데이터가 없습니다.</p>"
    min_v, max_v = min(values), max(values)
    if min_v == max_v:
        max_v += 1
    colors = {"ROLLING_EDGE_THROTTLE": "#2563eb", "BALANCED_GROWTH": "#16a34a"}
    lines = []
    labels = []
    for name, rows in series.items():
        points = []
        for idx, row in enumerate(rows):
            x = pad + idx / max(1, len(rows) - 1) * (width - pad * 2)
            y = height - pad - ((float(row.get(value_key, 0.0)) - min_v) / (max_v - min_v) * (height - pad * 2))
            points.append(f"{x:.1f},{y:.1f}")
        color = colors.get(name, "#64748b")
        lines.append(f"<polyline fill='none' stroke='{color}' stroke-width='3' points='{' '.join(points)}' />")
        labels.append(f"<span style='color:{color};font-weight:700'>{name}</span>")
    return f"<div>{' &nbsp; '.join(labels)}</div><svg class='chart' viewBox='0 0 {width} {height}' role='img' aria-label='{title}'><rect x='0' y='0' width='{width}' height='{height}' fill='white'/><line x1='{pad}' y1='{height-pad}' x2='{width-pad}' y2='{height-pad}' stroke='#cbd5e1'/><line x1='{pad}' y1='{pad}' x2='{pad}' y2='{height-pad}' stroke='#cbd5e1'/>{''.join(lines)}<text x='{pad}' y='22' font-size='13' fill='#334155'>{_fmt_value(max_v, value_key)}</text><text x='{pad}' y='{height-8}' font-size='13' fill='#334155'>{_fmt_value(min_v, value_key)}</text></svg>"


def _bar_chart(summary: dict[str, Any], period: str, title: str, limit: int | None = None) -> str:
    periods = summary.get("period_returns", {})
    rolling = {row["period"]: float(row.get("return_pct", 0.0)) for row in periods.get("ROLLING_EDGE_THROTTLE", {}).get(period, [])}
    balanced = {row["period"]: float(row.get("return_pct", 0.0)) for row in periods.get("BALANCED_GROWTH", {}).get(period, [])}
    keys = sorted(set(rolling) | set(balanced))
    if limit:
        keys = keys[-limit:]
    if not keys:
        return "<p>기간별 차트 데이터가 없습니다.</p>"
    width, height, pad = 1000, 300, 44
    values = [rolling.get(key, 0.0) for key in keys] + [balanced.get(key, 0.0) for key in keys]
    max_abs = max(abs(value) for value in values) or 1.0
    zero_y = height / 2
    group_w = (width - pad * 2) / max(1, len(keys))
    bar_w = max(3.0, min(14.0, group_w * 0.34))
    bars = []
    for idx, key in enumerate(keys):
        x = pad + idx * group_w + group_w / 2
        for offset, value, color in [(-bar_w / 1.8, rolling.get(key, 0.0), "#2563eb"), (bar_w / 1.8, balanced.get(key, 0.0), "#16a34a")]:
            h = abs(value) / max_abs * (height / 2 - pad)
            y = zero_y - h if value >= 0 else zero_y
            bars.append(f"<rect x='{x+offset-bar_w/2:.1f}' y='{y:.1f}' width='{bar_w:.1f}' height='{h:.1f}' fill='{color}' />")
    label_step = max(1, len(keys) // 12)
    labels = "".join(
        f"<text x='{pad + idx * group_w + group_w / 2:.1f}' y='{height-8}' font-size='10' text-anchor='middle' fill='#475569'>{key}</text>"
        for idx, key in enumerate(keys)
        if idx % label_step == 0
    )
    return (
        "<div><span style='color:#2563eb;font-weight:700'>Rolling Edge</span> &nbsp; "
        "<span style='color:#16a34a;font-weight:700'>Balanced Growth</span></div>"
        f"<svg class='chart' viewBox='0 0 {width} {height}' role='img' aria-label='{title}'>"
        f"<rect x='0' y='0' width='{width}' height='{height}' fill='white'/>"
        f"<line x1='{pad}' y1='{zero_y}' x2='{width-pad}' y2='{zero_y}' stroke='#94a3b8'/>"
        f"{''.join(bars)}{labels}"
        f"<text x='{pad}' y='20' font-size='13' fill='#334155'>+{max_abs:.1f}%</text>"
        f"<text x='{pad}' y='{height-24}' font-size='13' fill='#334155'>-{max_abs:.1f}%</text>"
        "</svg>"
    )


def _fmt_value(value: float, key: str) -> str:
    if key == "equity":
        return f"{value:,.0f}원"
    return f"{value:.2f}%"


def _money(value: Any) -> str:
    return f"{float(value or 0.0):,.0f}원"


def _pct(value: Any) -> str:
    return f"{float(value or 0.0):+.2f}%"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
