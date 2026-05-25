from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class DrawdownDefenseHTMLReport:
    def build(self, reports_dir: str = "docs/reports") -> dict[str, str]:
        root = Path(reports_dir)
        payload = _read(root / "latest_drawdown_defense_summary.json")
        path = root / "latest_drawdown_defense_report.html"
        path.write_text(_html(payload), encoding="utf-8")
        return {"html": str(path)}


def _html(payload: dict[str, Any]) -> str:
    scenarios = payload.get("scenarios", [])
    peak = payload.get("baseline_peak", {})
    trough = payload.get("baseline_trough", {})
    selected = payload.get("selected_defense", {})
    selected_capital = selected.get("capital", {})
    baseline = next((row for row in scenarios if row.get("scenario") == "BASELINE"), {})
    baseline_capital = baseline.get("capital", {})
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT 하락구간 방어 시스템 리포트</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body{{margin:0;font-family:Arial,'Malgun Gothic',sans-serif;background:#f8fafc;color:#172033}}
    header{{background:#111827;color:#fff;padding:28px}}main{{max-width:1180px;margin:auto;padding:20px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
    .card{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:16px}}.kpi{{font-size:24px;font-weight:800}}
    .warn{{background:#fffbeb;border-left:4px solid #f59e0b;padding:14px;margin:14px 0}}.good{{color:#047857}}.bad{{color:#b91c1c}}
    table{{width:100%;border-collapse:collapse;background:white;margin:14px 0}}th,td{{padding:10px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px}}th{{background:#eef2ff}}
    canvas{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:10px;max-height:330px}}
  </style>
</head>
<body>
  <header>
    <h1>ASTT 하락구간 방어 시스템 리포트</h1>
    <p>계좌 평가금이 줄어든 시기에서 어떤 대응 시스템이 필요했는지, 방어 엔진 적용 결과를 비교합니다.</p>
  </header>
  <main>
    <section class="warn"><strong>안전 고지:</strong> 이 분석은 기존 PAPER 거래일지를 재검증한 결과입니다. 실제 주문은 계속 금지이며 live_order_enabled는 false입니다.</section>
    <section class="grid">
      <div class="card"><div>기존 최종 평가금</div><div class="kpi">{_money(baseline_capital.get('final_equity_krw'))}</div></div>
      <div class="card"><div>방어 적용 최종 평가금</div><div class="kpi good">{_money(selected_capital.get('final_equity_krw'))}</div></div>
      <div class="card"><div>기존 최대 낙폭(MDD)</div><div class="kpi bad">{_pct(baseline_capital.get('max_drawdown_pct'))}</div></div>
      <div class="card"><div>방어 적용 최대 낙폭(MDD)</div><div class="kpi good">{_pct(selected_capital.get('max_drawdown_pct'))}</div></div>
      <div class="card"><div>하락구간 손실 감소</div><div class="kpi good">{_money(selected.get('comparison_to_baseline', {}).get('drawdown_window_loss_reduction_krw'))}</div></div>
      <div class="card"><div>최종 평가금 개선</div><div class="kpi good">{_money(selected.get('comparison_to_baseline', {}).get('final_equity_delta_krw'))}</div></div>
      <div class="card"><div>최고점</div><div class="kpi">{_money(peak.get('equity'))}</div><div>{html.escape(str(peak.get('time')))}</div></div>
      <div class="card"><div>저점</div><div class="kpi">{_money(trough.get('equity'))}</div><div>{html.escape(str(trough.get('time')))}</div></div>
    </section>
    <h2>시나리오 비교</h2>
    {_scenario_table(scenarios)}
    <h2>하락 원인 진단</h2>
    {_diagnosis_tables(payload.get('diagnosis', {}))}
    <h2>월별 시장 환경</h2>
    {_market_table(payload.get('market_month_metrics', {}))}
    <h2>방어 적용 곡선</h2>
    <canvas id="defenseChart"></canvas>
    <h2>결론</h2>
    <p>기본 채택 후보는 <strong>최근 20거래 성과 기반 자동 감속(Rolling Edge Throttle)</strong>입니다. 시장 약세를 이유로 무조건 쉬는 방식은 회복 기회를 많이 버렸고, 손실이 누적될 때 포지션 크기를 줄이는 방식이 더 균형적이었습니다.</p>
  </main>
  <script>
    const scenarioData = {json.dumps(_chart_data(scenarios), ensure_ascii=False)};
    new Chart(document.getElementById('defenseChart'), {{
      type: 'bar',
      data: {{
        labels: scenarioData.labels,
        datasets: [
          {{label: '최종 평가금 KRW', data: scenarioData.finalEquity, backgroundColor: '#16a34a'}},
          {{label: '최대 낙폭 %', data: scenarioData.mdd, backgroundColor: '#ef4444'}}
        ]
      }}
    }});
  </script>
</body>
</html>"""


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        capital = row.get("capital", {})
        window = row.get("drawdown_window", {})
        body.append(
            "<tr>"
            f"<td>{html.escape(row.get('scenario', ''))}</td>"
            f"<td>{int(capital.get('trade_count', 0))}</td>"
            f"<td>{_money(capital.get('final_equity_krw'))}</td>"
            f"<td>{_pct(capital.get('total_return_pct'))}</td>"
            f"<td>{_pct(capital.get('max_drawdown_pct'))}</td>"
            f"<td>{_money(window.get('total_pnl_krw'))}</td>"
            f"<td>{_money(row.get('comparison_to_baseline', {}).get('drawdown_window_loss_reduction_krw'))}</td>"
            f"<td>{int(window.get('throttled_trade_count', 0))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>방어 시나리오</th><th>거래 수</th><th>최종 평가금</th><th>총수익률</th><th>최대 낙폭</th><th>하락구간 손익</th><th>기존 대비 덜 잃은 금액</th><th>감속 거래</th></tr></thead><tbody>" + "".join(body) + "</tbody></table>"


def _diagnosis_tables(diagnosis: dict[str, Any]) -> str:
    return (
        f"<p>하락 구간 거래 수: <strong>{diagnosis.get('trade_count', 0)}</strong>, 손익: <strong>{_money(diagnosis.get('pnl_krw'))}</strong></p>"
        "<h3>전략별 손상</h3>" + _simple_table(diagnosis.get("by_strategy", []))
        + "<h3>셋업별 손상</h3>" + _simple_table(diagnosis.get("by_setup", []))
        + "<h3>손실 상위 종목</h3>" + _simple_table(diagnosis.get("worst_markets", []))
        + "<h3>연속 손실</h3>" + _simple_table(diagnosis.get("loss_streaks", []))
    )


def _market_table(metrics: dict[str, dict[str, Any]]) -> str:
    rows = []
    for month, row in sorted(metrics.items()):
        rows.append(
            f"<tr><td>{html.escape(month)}</td><td>{row.get('market_count', 0)}</td><td>{_pct(row.get('avg_return_pct'))}</td><td>{_pct(row.get('positive_market_pct'))}</td></tr>"
        )
    return "<table><thead><tr><th>월</th><th>마켓 수</th><th>평균 월간 수익률</th><th>상승 종목 비율</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _simple_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>표시할 데이터가 없습니다.</p>"
    keys = list(rows[0].keys())
    head = "".join(f"<th>{html.escape(str(key))}</th>" for key in keys)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(_format_cell(row.get(key)))}</td>" for key in keys) + "</tr>" for row in rows[:15])
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _chart_data(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "labels": [row.get("scenario") for row in rows],
        "finalEquity": [round(float(row.get("capital", {}).get("final_equity_krw", 0)), 2) for row in rows],
        "mdd": [round(float(row.get("capital", {}).get("max_drawdown_pct", 0)), 2) for row in rows],
    }


def _format_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _money(value: Any) -> str:
    return f"{float(value or 0):,.0f} KRW"


def _pct(value: Any) -> str:
    return f"{float(value or 0):+.2f}%"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
