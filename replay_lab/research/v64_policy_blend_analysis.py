from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v64_policy_blend_analyzer import analyze_v64_policy_blend


def build_v64_policy_blend_analysis(reports_dir: str = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    source = _read(root / "latest_true_walk_forward_summary.json")
    journal = source.get("journal", [])
    summary = analyze_v64_policy_blend(journal, float(source.get("capital", {}).get("initial_cash_krw", 500000.0)))
    _write(root / "latest_v64_policy_blend_analysis_summary.json", summary)
    _write_text(root / "latest_v64_policy_blend_analysis_report.html", _html(summary))
    return summary


def _html(summary: dict[str, Any]) -> str:
    rolling_vs_balanced = summary.get("rolling_vs_balanced", {})
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT V6.4 정책 조합 분석</title>
  <style>
    body{{margin:0;background:#f7f9fc;color:#172033;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.6}}
    header{{background:#0f172a;color:white;padding:30px 22px}}main{{max-width:1180px;margin:auto;padding:24px}}
    section,.card{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:16px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
    .kpi{{font-size:24px;font-weight:800;margin-top:4px}}.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
    table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left;vertical-align:top}}th{{background:#eef2ff}}
    .notice{{border-left:5px solid #d97706;background:#fffbeb;padding:13px 15px;border-radius:8px;margin-top:16px}}
  </style>
</head>
<body>
<header>
  <h1>ASTT V6.4 정책 조합 분석</h1>
  <p>Rolling Edge Throttle, Balanced Growth, Hybrid, Defensive, Aggressive를 서로 보완 가능한 운용 부품으로 비교합니다.</p>
</header>
<main>
  <div class="notice"><strong>안전 고지:</strong> 이 분석은 PAPER 모의투자 결과입니다. 실제 주문은 금지이며 real_order_enabled=false, live_order_allowed=false입니다.</div>
  <section>
    <h2>한눈에 보는 결론</h2>
    <p>Rolling Edge는 가장 단순하고 낙폭이 가장 낮은 기본 방어축입니다. Balanced Growth는 최종 평가금을 약간 더 높였지만, Plan A의 큰 승리를 일부 줄이고 Plan B/Combined의 손실을 줄이는 성격이 강합니다. 따라서 하나만 고정하기보다 <b>Rolling을 기본값</b>으로 두고, <b>Plan B/Combined 또는 애매한 PF 구간에서 Balanced 감속을 부분 적용</b>하는 방식이 더 실전적입니다.</p>
    <div class="grid">
      <div class="card"><div>Balanced - Rolling 최종 평가금 차이</div><div class="kpi good">{_money(rolling_vs_balanced.get('balanced_final_equity_delta_krw'))}</div></div>
      <div class="card"><div>수익률 차이</div><div class="kpi good">{_pct(rolling_vs_balanced.get('balanced_return_delta_pct_point'))}p</div></div>
      <div class="card"><div>최대 낙폭 차이</div><div class="kpi warn">{_pct(rolling_vs_balanced.get('balanced_mdd_delta_pct_point'))}p</div></div>
      <div class="card"><div>PF 차이</div><div class="kpi good">{float(rolling_vs_balanced.get('balanced_profit_factor_delta', 0.0)):.3f}</div></div>
    </div>
  </section>
  <section><h2>시나리오 전체 비교</h2>{_scenario_table(summary.get('scenarios', []))}</section>
  <section><h2>Rolling vs Balanced: 손익 차이</h2>
    <p>Balanced가 더 좋았던 달은 주로 약한 성과 구간에서 70% 감속이 손실을 줄인 경우입니다. Rolling이 더 좋았던 달은 Plan A fat-tail 승리를 더 크게 살린 경우가 많았습니다.</p>
    <h3>Balanced가 유리했던 달</h3>{_delta_table(summary.get('top_months_balanced_better', []), '월')}
    <h3>Rolling이 유리했던 달</h3>{_delta_table(summary.get('top_months_rolling_better', []), '월')}
  </section>
  <section><h2>플랜/전략별 보완 포인트</h2>
    <h3>Plan별 차이</h3>{_delta_table(summary.get('plan_deltas_balanced_minus_rolling', []), 'Plan')}
    <h3>Strategy별 차이</h3>{_delta_table(summary.get('strategy_deltas_balanced_minus_rolling', []), 'Strategy')}
    <h3>Setup별 차이</h3>{_delta_table(summary.get('setup_deltas_balanced_minus_rolling', [])[:10], 'Setup')}
  </section>
  <section><h2>정책별 장단점과 채택안</h2>{_recommendation_table(summary.get('recommended_policy_stack', []))}</section>
  <section><h2>정책 발동 현황</h2>{_activity_table(summary.get('policy_activity', {}))}</section>
</main>
</body>
</html>"""


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{row.get('scenario')}</td><td>{_money(row.get('final_equity_krw'))}</td><td>{_pct(row.get('return_pct'))}</td><td>{_pct(row.get('mdd_pct'))}</td><td>{float(row.get('profit_factor', 0.0)):.3f}</td><td>{int(row.get('trade_count', 0))}</td><td>{float(row.get('return_mdd_ratio', 0.0)):.2f}</td></tr>"
        for row in rows
    )
    return f"<table><tr><th>Scenario</th><th>최종 평가금</th><th>수익률</th><th>MDD</th><th>PF</th><th>거래수</th><th>Return/MDD</th></tr>{body}</table>"


def _delta_table(rows: list[dict[str, Any]], label: str) -> str:
    body = "".join(
        f"<tr><td>{row.get('key')}</td><td>{_money(row.get('balanced_value_krw'))}</td><td>{_money(row.get('rolling_value_krw'))}</td><td>{_money(row.get('delta_krw'))}</td></tr>"
        for row in rows
    )
    return f"<table><tr><th>{label}</th><th>Balanced 손익</th><th>Rolling 손익</th><th>Balanced-Rolling</th></tr>{body}</table>"


def _recommendation_table(rows: list[dict[str, str]]) -> str:
    body = "".join(f"<tr><td>{row.get('policy')}</td><td>{row.get('recommendation')}</td><td>{row.get('reason')}</td></tr>" for row in rows)
    return f"<table><tr><th>역할</th><th>추천</th><th>이유</th></tr>{body}</table>"


def _activity_table(activity: dict[str, Any]) -> str:
    body = "".join(
        f"<tr><td>{name}</td><td>{data.get('actions')}</td><td>{data.get('states')}</td><td>{data.get('multipliers')}</td><td>{data.get('top_reasons')}</td></tr>"
        for name, data in activity.items()
    )
    return f"<table><tr><th>정책</th><th>진입/스킵</th><th>상태</th><th>배수</th><th>주요 사유</th></tr>{body}</table>"


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
