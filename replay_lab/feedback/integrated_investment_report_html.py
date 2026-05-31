from __future__ import annotations

import json
from collections import defaultdict
from html import escape
from pathlib import Path
from typing import Any


class IntegratedInvestmentReportHTML:
    def build(self, output_dir: str = "docs/reports") -> dict[str, str]:
        root = Path(output_dir)
        payload = build_integrated_investment_summary(root)
        summary_path = root / "latest_integrated_investment_summary.json"
        report_path = root / "latest_v62_full_investment_report.html"
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        report_path.write_text(render_integrated_investment_report(payload), encoding="utf-8")
        return {"html": str(report_path), "summary": str(summary_path)}


def build_integrated_investment_summary(root: Path) -> dict[str, Any]:
    v62 = _read_json(root / "latest_v62_full_investment_summary.json")
    v673_matrix = _read_json(root / "latest_v673_agent_matrix_summary.json")
    v673_router = _read_json(root / "latest_v673_scenario_router_summary.json")
    v673_data = _read_json(root / "latest_v673_dominance_data_quality_summary.json")
    v673_hwm = _read_json(root / "latest_v673_high_watermark_summary.json")
    v673_review = _read_json(root / "latest_head_controller_v673_review_summary.json")
    v64_compounding = _read_json(root / "latest_v64_policy_compounding_summary.json")
    v681_audit = _read_json(root / "latest_v681_reconciliation_audit_summary.json")
    v681_dominance = _read_json(root / "latest_v681_compounding_dominance_summary.json")
    v681_bear = _read_json(root / "latest_v681_bear_compounding_agent_summary.json")
    v681_router = _read_json(root / "latest_v681_compounding_router_summary.json")
    v681_control = _read_json(root / "latest_v681_control_tower_summary.json")
    v681_paper = _read_json(root / "latest_v681_paper_runtime_summary.json")
    v681_loss_guard = _read_json(root / "latest_v681_loss_guard_insight_summary.json")
    v682_defense = _read_json(root / "latest_v682_bear_defense_insight_summary.json")
    v682_bounce = _read_json(root / "latest_v682_bear_bounce_summary.json")
    v682_router = _read_json(root / "latest_v682_bear_response_router_summary.json")
    v682_cases = _read_json(root / "latest_v682_bounce_case_study_summary.json")
    v683_runtime = _read_json(root / "latest_v683_paper_runtime_summary.json")
    v683_backfill = _read_json(root / "latest_v683_backfill_20260101_summary.json")
    v683_comparison = _read_json(root / "latest_v683_active_shadow_comparison_summary.json")
    v683_control = _read_json(root / "latest_v683_control_tower_summary.json")
    forward = _forward_status(root)
    journal = list(v62.get("journal") or _read_json(root / "latest_true_walk_forward_summary.json").get("journal", []))
    daily = _daily_rows(journal)
    weekly = _period_rows(daily, "week")
    monthly = _period_rows(daily, "month")
    capital = v62.get("capital", {})
    scenario_period_records = dict(v673_matrix.get("period_records") or {})
    router_rows = v673_router.get("scenarios", [])
    matrix_rows = v673_matrix.get("scenarios", [])
    all_scenarios = _scenario_rows(matrix_rows, router_rows, scenario_period_records)
    router = next((row for row in all_scenarios if row.get("scenario") == "SCENARIO_AGENT_ROUTER_V1"), {})
    baseline = next((row for row in all_scenarios if row.get("scenario") == "POLICY_BLEND_CONTROL"), capital)
    payload = {
        "schema_version": "integrated_investment_report_v2",
        "title": "ASTT 통합 투자 검증 리포트",
        "generated_from": {
            "v62_full_investment": bool(v62),
            "v673_dominance_router": bool(v673_router or v673_matrix),
            "v68_forward_paper_plan": True,
        },
        "safety": {
            "real_order_enabled": False,
            "live_order_allowed": False,
            "auto_apply_allowed": False,
            "final_status": v673_review.get("final_decision") or "LIVE_NOT_ALLOWED",
        },
        "capital": capital,
        "daily_rows": daily,
        "weekly_rows": weekly,
        "monthly_rows": monthly,
        "strategy_contribution": v62.get("strategy_contribution", []),
        "plan_performance": v62.get("plan_performance", []),
        "risk": v62.get("risk", {}),
        "policy_compounding": _policy_compounding_payload(v64_compounding),
        "v681": {
            "reconciliation": v681_audit,
            "compounding_dominance": v681_dominance,
            "bear_agents": v681_bear,
            "router": v681_router,
            "control_tower": v681_control,
            "paper_runtime": v681_paper,
            "loss_guard": v681_loss_guard,
        },
        "v682": {
            "bear_defense": v682_defense,
            "bear_bounce": v682_bounce,
            "bear_response_router": v682_router,
            "bounce_cases": v682_cases,
        },
        "v683": {
            "runtime": v683_runtime,
            "backfill": v683_backfill,
            "active_shadow": v683_comparison,
            "control_tower": v683_control,
        },
        "dominance": {
            "data_quality": v673_data,
            "matrix": matrix_rows,
            "router_baseline": baseline,
            "router": router,
            "scenario_rows": all_scenarios,
            "scenario_period_records": scenario_period_records,
            "scenario_monthly_comparison": _scenario_monthly_comparison(scenario_period_records),
            "market_state_pnl": v673_router.get("market_state_pnl", v673_matrix.get("market_state_pnl", [])),
            "high_watermark": v673_hwm,
            "review": v673_review,
        },
        "forward_shadow_paper": forward,
        "plain_language": _plain_language(capital, baseline, router, v673_router.get("market_state_pnl", v673_matrix.get("market_state_pnl", [])), forward),
    }
    (root / "latest_v62_daily_summary.json").write_text(json.dumps({"daily_rows": daily}, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "latest_v62_weekly_summary.json").write_text(json.dumps({"weekly_rows": weekly}, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "latest_v62_monthly_summary.json").write_text(json.dumps({"monthly_rows": monthly}, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def render_integrated_investment_report(payload: dict[str, Any]) -> str:
    capital = payload.get("capital", {})
    daily = payload.get("daily_rows", [])
    weekly = payload.get("weekly_rows", [])
    monthly = payload.get("monthly_rows", [])
    dominance = payload.get("dominance", {})
    compounding = payload.get("policy_compounding", {})
    v681 = payload.get("v681", {})
    v681_loss_guard = v681.get("loss_guard", {})
    v682 = payload.get("v682", {})
    v683 = payload.get("v683", {})
    router = dominance.get("router", {})
    baseline = dominance.get("router_baseline", {})
    safety = payload.get("safety", {})
    scenario_records = dominance.get("scenario_period_records", {})
    scenario_rows = dominance.get("scenario_rows", [])
    monthly_chart = _line_chart(monthly, "period", "end_equity_krw", "월별 계좌 변화")
    drawdown_chart = _line_chart(monthly, "period", "mdd_pct", "월별 최대 하락률", invert=True)
    state_chart = _bar_chart(dominance.get("market_state_pnl", []), "market_state", "pnl_krw", "시장 상태별 손익")
    scenario_json = _json_script({"records": scenario_records, "scenarios": scenario_rows})
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT 통합 투자 검증 리포트</title>
  <style>
    :root {{
      --bg:#f6f7f9; --panel:#ffffff; --ink:#172033; --muted:#667085; --line:#d8dee8;
      --good:#047857; --bad:#b42318; --warn:#b45309; --accent:#155eef; --soft:#eff6ff;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Arial,"Malgun Gothic",sans-serif; line-height:1.62; }}
    header {{ background:#111827; color:#fff; padding:30px 24px; }}
    main {{ max-width:1280px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 8px; font-size:32px; letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:22px; }}
    h3 {{ margin:0 0 8px; font-size:16px; }}
    section {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:18px; margin:16px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .metric {{ border:1px solid var(--line); border-radius:8px; padding:14px; background:#fbfcfe; min-height:86px; }}
    .metric span {{ display:block; color:var(--muted); font-size:13px; }}
    .metric strong {{ display:block; margin-top:5px; font-size:24px; }}
    .notice {{ border-left:5px solid var(--warn); background:#fffbeb; padding:12px 14px; border-radius:6px; }}
    .toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0 14px; }}
    .toolbar select {{ min-width:320px; max-width:100%; padding:9px 10px; border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); }}
    .ok {{ color:var(--good); font-weight:700; }} .bad {{ color:var(--bad); font-weight:700; }} .muted {{ color:var(--muted); }}
    .table-wrap {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th,td {{ border-bottom:1px solid var(--line); padding:9px 10px; text-align:right; white-space:nowrap; }}
    th:first-child,td:first-child {{ text-align:left; }}
    th {{ background:#f2f4f7; color:#344054; }}
    tr.month-row {{ cursor:pointer; }}
    tr.month-row:hover {{ background:var(--soft); }}
    tr.week-row td {{ background:#fbfcfe; }}
    tr.day-row td {{ background:#fff; color:#344054; font-size:13px; }}
    .indent-week {{ padding-left:24px; }}
    .indent-day {{ padding-left:48px; }}
    .two {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .chart {{ width:100%; min-height:220px; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .small {{ font-size:13px; }}
    @media(max-width:900px) {{ .grid,.two {{ grid-template-columns:1fr; }} main {{ padding:14px; }} .toolbar select {{ min-width:100%; }} }}
  </style>
</head>
<body>
<header>
  <h1>ASTT 통합 투자 검증 리포트</h1>
  <p>2022년부터 현재까지의 월/주/일 투자 기록과 도미넌스 Route Agent 검증을 한 화면에서 관리합니다.</p>
</header>
<main>
  <section class="notice">
    <strong>안전 상태:</strong>
    real_order_enabled={_bool_text(safety.get("real_order_enabled"))},
    live_order_allowed={_bool_text(safety.get("live_order_allowed"))},
    auto_apply_allowed={_bool_text(safety.get("auto_apply_allowed"))}.
    최종 상태: <strong>{_esc(safety.get("final_status"))}</strong>
  </section>

  <section>
    <h2>한눈에 보는 결론</h2>
    <div class="grid">
      {_metric("기존 전체 검증 최종 자산", _money(capital.get("final_equity_krw")))}
      {_metric("기존 전체 수익률", _pct(capital.get("total_return_pct")))}
      {_metric("기존 최대 하락률", _pct(capital.get("max_drawdown_pct")))}
      {_metric("거래 수", _num(capital.get("trade_count")))}
      {_metric("도미넌스 Router 최종 자산", _money(router.get("final_equity_krw")))}
      {_metric("도미넌스 Router 수익률", _pct(router.get("total_return_pct")))}
      {_metric("도미넌스 Router MDD", _pct(router.get("mdd_pct")))}
      {_metric("Forward Paper 상태", _esc(payload.get("forward_shadow_paper", {}).get("status")))}
    </div>
    <p>{_esc(payload.get("plain_language", {}).get("headline"))}</p>
  </section>

  <section>
    <h2>Rolling/Balanced 복리 재투자 검증</h2>
    <p class="muted">원금과 수익을 다음 거래 포지션 산정에 다시 반영한 V6.4 진짜 복리 검증입니다. 150만원 이상 도달한 시나리오는 이 섹션에 있습니다.</p>
    <div class="grid">
      {_metric("Rolling 복리 최종 자산", _money(compounding.get("rolling", {}).get("final_equity_krw")))}
      {_metric("Rolling 복리 수익률", _pct(compounding.get("rolling", {}).get("return_pct")))}
      {_metric("Balanced 복리 최종 자산", _money(compounding.get("balanced", {}).get("final_equity_krw")))}
      {_metric("Balanced 복리 수익률", _pct(compounding.get("balanced", {}).get("return_pct")))}
    </div>
    {_table(compounding.get("scenarios", []), ["scenario", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count"])}
    <p><a href="latest_v64_policy_compounding_report.html">Rolling/Balanced 복리 상세 리포트 열기</a></p>
  </section>

  <section>
    <h2>V6.8.1 최강 복리 기준선 + 도미넌스 재검증</h2>
    <p class="muted">V6.4와 같은 복리 ledger로 다시 계산한 공식 비교입니다. V6.7.3의 90만원대 결과와 직접 비교하지 않습니다.</p>
    <div class="grid">
      {_metric("Ledger 감사 결론", _esc(v681.get("reconciliation", {}).get("conclusion")))}
      {_metric("도미넌스 사용 판정", _esc(v681.get("compounding_dominance", {}).get("decision")))}
      {_metric("Control Tower", _esc(v681.get("control_tower", {}).get("decision")))}
      {_metric("Paper 현재 자산", _money(v681.get("paper_runtime", {}).get("current_equity_krw")))}
    </div>
    {_table(v681.get("compounding_dominance", {}).get("scenarios", []), ["scenario", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "return_mdd_ratio", "saved_loss_krw", "missed_profit_krw", "net_effect_krw", "decision"])}
    <p><a href="latest_v681_compounding_dominance_report.html">V6.8.1 복리+도미넌스 상세</a> / <a href="latest_v681_reconciliation_audit_report.html">Ledger 감사</a></p>
  </section>

  <section>
    <h2>V6.8.1 하락장 Agent / 통합 Router / Forward Paper</h2>
    <div class="two">
      <div>{_table(v681.get("bear_agents", {}).get("scenarios", []), ["scenario", "final_equity_krw", "return_pct", "mdd_pct", "return_2025_pct", "return_2026_pct", "decision"])}</div>
      <div>{_table(v681.get("router", {}).get("scenarios", []), ["scenario", "final_equity_krw", "return_pct", "mdd_pct", "return_mdd_ratio", "hwm_score", "giveback_ratio_pct", "decision"])}</div>
    </div>
    {_table([v681.get("paper_runtime", {})], ["active_route", "start_date", "current_equity_krw", "current_cash_krw", "open_positions", "today_pnl_krw", "weekly_pnl_krw", "monthly_pnl_krw", "healthcheck"])}
    <p><a href="latest_v681_bear_compounding_agent_report.html">Bear Agent</a> / <a href="latest_v681_compounding_router_report.html">Router</a> / <a href="latest_v681_paper_runtime_report.html">Paper Runtime</a> / <a href="latest_v681_control_tower_report.html">Control Tower</a></p>
  </section>

  <section>
    <h2>V6.8.1 Loss Guard Insight / 2026 Route Candidate</h2>
    <p class="muted">2022-present trade records were rechecked to find non-random defensive edges. This section is shadow-paper only and does not enable live orders.</p>
    {_table(v681_loss_guard.get("new_candidate_rows", []), ["start", "scenario", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "return_mdd_ratio", "skipped_trade_count", "average_multiplier"])}
    {_table(v681_loss_guard.get("monthly_2026_winners", []), ["period", "best", "best_return_pct", "worst", "worst_return_pct", "spread_pct"])}
    <p><a href="latest_v681_loss_guard_insight_report.html">Loss Guard Insight detail</a></p>
  </section>

  <section>
    <h2>V6.8.2 Bear Defense / Bear Bounce Verification</h2>
    <p class="muted">This expands the loss-defense test into bear-market defense, bear-bounce research, and a full bear-response router. It remains paper/shadow only.</p>
    <div class="grid">
      {_metric("Bear Defense", _esc(v682.get("bear_defense", {}).get("decision")))}
      {_metric("Bear Bounce", _esc(v682.get("bear_bounce", {}).get("decision")))}
      {_metric("Bear Router", _esc(v682.get("bear_response_router", {}).get("decision")))}
      {_metric("Active Applied", _esc(v682.get("bear_response_router", {}).get("active_route_change_applied")))}
    </div>
    {_table(v682.get("bear_response_router", {}).get("scenarios", []), ["scenario", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "return_mdd_ratio", "return_2025_pct", "return_2026_pct", "bounce_trade_count", "net_effect_krw", "decision"])}
    {_table([v682.get("bear_bounce", {}).get("bounce_metrics", {})], ["bounce_candidates", "bounce_entries", "bounce_win_rate_pct", "avg_bounce_pnl_krw", "net_bounce_pnl_krw", "best_bounce_krw", "worst_bounce_krw", "tp_count", "sl_count"])}
    <p><a href="latest_v682_bear_defense_insight_report.html">Bear Defense detail</a> / <a href="latest_v682_bear_bounce_report.html">Bear Bounce detail</a> / <a href="latest_v682_bear_response_router_report.html">Bear Response Router</a> / <a href="latest_v682_bounce_case_study_report.html">Bounce cases</a></p>
  </section>

  <section>
    <h2>V6.8.3 Live-Forward Paper Runtime</h2>
    <p class="muted">2026-01-01 backfill rebuilt the active paper account and four shadow ledgers. Live order permissions remain disabled and route switching is locked.</p>
    <div class="grid">
      {_metric("Active Route", _esc(v683.get("runtime", {}).get("active_route")))}
      {_metric("Current Equity", _money(v683.get("runtime", {}).get("current_equity_krw")))}
      {_metric("Healthcheck", _esc(v683.get("runtime", {}).get("healthcheck")))}
      {_metric("Control Tower", _esc(v683.get("control_tower", {}).get("latest_recommendation")))}
    </div>
    {_table(v683.get("backfill", {}).get("routes", []), ["scenario", "route_status", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count", "win_rate_pct", "net_effect_krw", "decision"])}
    {_table(v683.get("active_shadow", {}).get("rows", []), ["route", "status", "equity", "mdd_pct", "return_delta_vs_active_pct", "comment"])}
    <p><a href="latest_v683_backfill_20260101_report.html">V683 Backfill</a> / <a href="latest_v683_paper_runtime_report.html">Runtime</a> / <a href="latest_v683_active_shadow_comparison_report.html">Active vs Shadow</a> / <a href="latest_v683_control_tower_report.html">Control Tower</a> / <a href="astt_report_dashboard.html">Dashboard</a></p>
  </section>

  <section>
    <h2>시나리오별 투자 기록</h2>
    <div class="toolbar">
      <label for="scenarioSelect"><strong>시나리오 선택</strong></label>
      <select id="scenarioSelect"></select>
    </div>
    <div id="scenarioMetrics" class="grid"></div>
    <p class="muted">월을 클릭하면 그 월에 속한 주 단위, 일 단위 기록이 아래로 펼쳐집니다. 표의 데이터는 V6.7.3 도미넌스 포함 검증 기록입니다.</p>
    <div id="scenarioDrilldown"></div>
  </section>

  <section>
    <h2>시나리오별 월 변화량 비교</h2>
    <p class="muted">월별 수익률을 나란히 비교합니다. Rolling/Balanced 단독보다 Policy Blend 계열이 강한지 확인하는 용도입니다.</p>
    {_table(dominance.get("scenario_monthly_comparison", []), ["period", "ROLLING_ONLY_CONTROL", "ROLLING_ONLY_DOMINANCE_OVERLAY", "BALANCED_ONLY_CONTROL", "BALANCED_ONLY_DOMINANCE_OVERLAY", "POLICY_BLEND_CONTROL", "POLICY_BLEND_DOMINANCE_OVERLAY", "SCENARIO_AGENT_ROUTER_V1"])}
  </section>

  <section>
    <h2>기존 V62 월 단위 투자 기록</h2>
    {monthly_chart}
    {_table(monthly, ["period", "trade_count", "win_rate", "start_equity_krw", "end_equity_krw", "return_pct", "mdd_pct"])}
  </section>

  <section>
    <h2>기존 V62 주/일 단위 기록</h2>
    <div class="two">
      <div>{_table(weekly[-26:], ["period", "trade_count", "win_rate", "start_equity_krw", "end_equity_krw", "return_pct", "mdd_pct"])}</div>
      <div>{_table(daily[-120:], ["date", "trade_count", "win_rate", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "drawdown_pct"])}</div>
    </div>
  </section>

  <section>
    <h2>그래프로 보는 위험</h2>
    <div class="two"><div>{drawdown_chart}</div><div>{state_chart}</div></div>
  </section>

  <section>
    <h2>도미넌스 반영 Route Agent 검증</h2>
    <p>{_esc(payload.get("plain_language", {}).get("dominance"))}</p>
    {_table(scenario_rows, ["scenario", "final_equity_krw", "total_return_pct", "mdd_pct", "trade_count", "decision"])}
    <h3>시장 상태별 해석</h3>
    {_table(dominance.get("market_state_pnl", []), ["market_state", "trade_count", "pnl_krw", "decision"])}
  </section>

  <section>
    <h2>전략/플랜별 기여</h2>
    <div class="two">
      <div>{_table(payload.get("strategy_contribution", []), ["strategy", "trade_count", "pnl_krw", "win_rate", "profit_factor", "decision"])}</div>
      <div>{_table(payload.get("plan_performance", []), ["plan", "trade_count", "pnl_krw", "win_rate", "profit_factor", "decision"])}</div>
    </div>
  </section>

  <section>
    <h2>Forward Shadow Paper 준비 상태</h2>
    <p>{_esc(payload.get("plain_language", {}).get("forward"))}</p>
    {_table([payload.get("forward_shadow_paper", {})], ["status", "active_route", "candidate_route", "backfill_start", "server_ready", "manual_switch_required"])}
  </section>

  <section>
    <h2>관리용 링크</h2>
    <ul>
      <li><a href="latest_v673_scenario_router_report.html">도미넌스 Router 세부 리포트</a></li>
      <li><a href="latest_v673_high_watermark_report.html">고점 방어 세부 리포트</a></li>
      <li><a href="astt_report_dashboard.html">전체 리포트 목록</a></li>
    </ul>
  </section>
</main>
<script id="scenario-data" type="application/json">{scenario_json}</script>
<script>
const scenarioPayload = JSON.parse(document.getElementById("scenario-data").textContent);
const records = scenarioPayload.records || {{}};
const scenarios = scenarioPayload.scenarios || [];
const selectEl = document.getElementById("scenarioSelect");
const metricsEl = document.getElementById("scenarioMetrics");
const drillEl = document.getElementById("scenarioDrilldown");
let openMonth = null;

function fmtMoney(value) {{
  const n = Number(value || 0);
  return new Intl.NumberFormat("ko-KR", {{ maximumFractionDigits: 0 }}).format(n) + "원";
}}
function fmtPct(value) {{
  const n = Number(value || 0);
  return (n >= 0 ? "+" : "") + n.toFixed(2) + "%";
}}
function esc(value) {{
  return String(value ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[ch]));
}}
function metric(label, value) {{
  return `<div class="metric"><span>${{esc(label)}}</span><strong>${{value}}</strong></div>`;
}}
function rowCells(row, firstLabel, firstClass) {{
  return `<td class="${{firstClass || ""}}">${{esc(firstLabel)}}</td>
    <td>${{Number(row.trade_count || 0).toLocaleString("ko-KR")}}</td>
    <td>${{fmtPct((Number(row.win_rate || 0) <= 1 ? Number(row.win_rate || 0) * 100 : Number(row.win_rate || 0)))}}</td>
    <td>${{fmtMoney(row.start_equity_krw)}}</td>
    <td>${{fmtMoney(row.end_equity_krw)}}</td>
    <td>${{fmtMoney(row.pnl_krw)}}</td>
    <td>${{fmtPct(row.return_pct)}}</td>
    <td>${{fmtPct(row.mdd_pct ?? row.drawdown_pct)}}</td>
    <td>${{esc(row.dominant_market_state || "")}}</td>
    <td>${{esc(row.selected_agent || "")}}</td>`;
}}
function monthOf(row) {{
  return String(row.period || row.date || "").slice(0, 7);
}}
function weekInMonth(row, month) {{
  return String(row.start_date || row.date || "").slice(0, 7) === month;
}}
function renderScenario() {{
  const name = selectEl.value;
  const summary = scenarios.find(row => row.scenario === name) || {{}};
  const data = records[name] || {{}};
  const monthly = data.monthly || [];
  const weekly = data.weekly || [];
  const daily = data.daily || [];
  metricsEl.innerHTML = [
    metric("선택 시나리오", esc(name)),
    metric("최종 자산", fmtMoney(summary.final_equity_krw)),
    metric("총 수익률", fmtPct(summary.total_return_pct)),
    metric("최대 하락률", fmtPct(summary.mdd_pct)),
  ].join("");
  if (!monthly.length) {{
    drillEl.innerHTML = `<p class="muted">이 시나리오는 월/주/일 기록이 아직 없습니다. V6.7.3 matrix 재생성이 필요합니다.</p>`;
    return;
  }}
  let html = `<div class="table-wrap"><table><thead><tr>
    <th>기간</th><th>거래 수</th><th>승률</th><th>시작 자산</th><th>종료 자산</th><th>손익</th><th>수익률</th><th>MDD</th><th>시장 상태</th><th>Agent</th>
  </tr></thead><tbody>`;
  monthly.forEach(month => {{
    const period = String(month.period);
    const opened = openMonth === period;
    html += `<tr class="month-row" data-period="${{esc(period)}}"><td>${{opened ? "▼" : "▶"}} ${{esc(period)}}</td>${{rowCells(month, period).replace(/^<td[^>]*>.*?<\\/td>/, "")}}</tr>`;
    if (opened) {{
      weekly.filter(row => weekInMonth(row, period)).forEach(week => {{
        html += `<tr class="week-row"><td class="indent-week">주: ${{esc(week.period)}} (${{esc(week.start_date)}}~${{esc(week.end_date)}})</td>${{rowCells(week, week.period).replace(/^<td[^>]*>.*?<\\/td>/, "")}}</tr>`;
      }});
      daily.filter(row => monthOf(row) === period).forEach(day => {{
        html += `<tr class="day-row"><td class="indent-day">일: ${{esc(day.period || day.date)}}</td>${{rowCells(day, day.period || day.date).replace(/^<td[^>]*>.*?<\\/td>/, "")}}</tr>`;
      }});
    }}
  }});
  html += `</tbody></table></div>`;
  drillEl.innerHTML = html;
  drillEl.querySelectorAll(".month-row").forEach(row => {{
    row.addEventListener("click", () => {{
      const period = row.getAttribute("data-period");
      openMonth = openMonth === period ? null : period;
      renderScenario();
    }});
  }});
}}
function initScenario() {{
  const names = Object.keys(records);
  const preferred = names.includes("SCENARIO_AGENT_ROUTER_V1") ? "SCENARIO_AGENT_ROUTER_V1" : names[0];
  selectEl.innerHTML = names.map(name => `<option value="${{esc(name)}}">${{esc(name)}}</option>`).join("");
  if (preferred) selectEl.value = preferred;
  selectEl.addEventListener("change", () => {{ openMonth = null; renderScenario(); }});
  renderScenario();
}}
initScenario();
</script>
</body>
</html>"""


def _scenario_rows(matrix_rows: list[dict[str, Any]], router_rows: list[dict[str, Any]], period_records: dict[str, Any]) -> list[dict[str, Any]]:
    by_name = {str(row.get("scenario")): row for row in matrix_rows + router_rows if row.get("scenario")}
    for name in period_records:
        by_name.setdefault(name, {"scenario": name})
    return [by_name[name] for name in sorted(by_name)]


def _scenario_monthly_comparison(period_records: dict[str, dict[str, list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    periods = sorted({str(row.get("period")) for data in period_records.values() for row in data.get("monthly", []) if row.get("period")})
    out = []
    for period in periods:
        item: dict[str, Any] = {"period": period}
        for scenario, data in period_records.items():
            row = next((r for r in data.get("monthly", []) if r.get("period") == period), None)
            if row:
                item[scenario] = row.get("return_pct")
        out.append(item)
    return out


def _policy_compounding_payload(summary: dict[str, Any]) -> dict[str, Any]:
    scenarios = list(summary.get("scenarios", []))
    rolling = next((row for row in scenarios if row.get("scenario") == "ROLLING_EDGE_THROTTLE"), {})
    balanced = next((row for row in scenarios if row.get("scenario") == "BALANCED_GROWTH"), {})
    return {
        "schema_version": summary.get("schema_version"),
        "description": summary.get("description"),
        "scenarios": scenarios,
        "rolling": rolling,
        "balanced": balanced,
        "rolling_vs_balanced": summary.get("rolling_vs_balanced", {}),
        "recommendation": summary.get("recommendation", {}),
        "report_link": "latest_v64_policy_compounding_report.html",
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _daily_rows(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        date = str(row.get("date") or row.get("entry_time", ""))[:10]
        if date:
            groups[date].append(row)
    rows = []
    for date, items in sorted(groups.items()):
        start = _float(items[0].get("equity_before"))
        end = _float(items[-1].get("equity_after"))
        pnl = sum(_float(row.get("pnl_krw")) for row in items)
        wins = sum(1 for row in items if _float(row.get("pnl_krw")) > 0)
        peak = max(_float(row.get("equity_before")) for row in items) if items else start
        trough = min(_float(row.get("equity_after")) for row in items) if items else end
        rows.append(
            {
                "date": date,
                "trade_count": len(items),
                "wins": wins,
                "win_rate": wins / len(items) if items else 0.0,
                "start_equity_krw": start,
                "end_equity_krw": end,
                "pnl_krw": pnl,
                "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
                "drawdown_pct": (trough / peak - 1.0) * 100.0 if peak else 0.0,
            }
        )
    return rows


def _period_rows(daily: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in daily:
        ts = _date_key(row["date"], kind)
        groups[ts].append(row)
    rows = []
    for period, items in sorted(groups.items()):
        start = _float(items[0].get("start_equity_krw"))
        end = _float(items[-1].get("end_equity_krw"))
        trades = sum(int(row.get("trade_count", 0)) for row in items)
        wins = sum(int(row.get("wins", 0)) for row in items)
        rows.append(
            {
                "period": period,
                "days": len(items),
                "trade_count": trades,
                "win_rate": wins / trades if trades else 0.0,
                "start_equity_krw": start,
                "end_equity_krw": end,
                "pnl_krw": sum(_float(row.get("pnl_krw")) for row in items),
                "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
                "mdd_pct": min((_float(row.get("drawdown_pct")) for row in items), default=0.0),
            }
        )
    return rows


def _date_key(value: str, kind: str) -> str:
    from datetime import date

    y, m, d = [int(part) for part in value.split("-")]
    day = date(y, m, d)
    if kind == "month":
        return f"{day.year:04d}-{day.month:02d}"
    iso = day.isocalendar()
    return f"{iso.year:04d}-W{iso.week:02d}"


def _forward_status(root: Path) -> dict[str, Any]:
    forward_files = [
        root / "latest_tradable_source_forward_summary.json",
        root / "latest_redesigned_source_forward_summary.json",
        root / "latest_forward_micro_summary.json",
    ]
    available = [path.name for path in forward_files if path.exists()]
    return {
        "status": "준비 필요" if not available else "기존 forward 자료 있음",
        "active_route": "PAPER_ROUTE_V1_BASE",
        "candidate_route": "SCENARIO_AGENT_ROUTER_V1",
        "backfill_start": "2026-01-01",
        "server_ready": False,
        "manual_switch_required": True,
        "available_forward_files": available,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _plain_language(capital: dict[str, Any], baseline: dict[str, Any], router: dict[str, Any], states: list[dict[str, Any]], forward: dict[str, Any]) -> dict[str, str]:
    base_ret = _float(baseline.get("total_return_pct", capital.get("total_return_pct")))
    router_ret = _float(router.get("total_return_pct"))
    weak_states = [row.get("market_state") for row in states if row.get("decision") == "DEFENSE_REQUIRED"]
    return {
        "headline": f"현재 검증 기준으로 도미넌스 Router는 Policy Blend 기준 대비 수익률을 {router_ret - base_ret:+.2f}%p 변화시켰습니다.",
        "dominance": "도미넌스 포함 검증입니다. Rolling/Balanced 단독은 비교군이고, 실제 후보는 Policy Blend Dominance Overlay와 Scenario Agent Router입니다. 방어가 필요한 상태: " + (", ".join(str(x) for x in weak_states) or "없음"),
        "forward": "다음 단계는 2026-01-01 기준 paper backfill을 만들고, 이후 live forward shadow paper를 누적하는 것입니다. 자동 실전 전환은 금지입니다." if not forward.get("server_ready") else "Forward paper 서버 자료가 연결되어 있습니다.",
    }


def _table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return "<p class=\"muted\">표시할 데이터가 없습니다.</p>"
    head = "".join(f"<th>{_label(key)}</th>" for key in keys)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{_display(row.get(key), key)}</td>" for key in keys) + "</tr>"
    return f"<div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _line_chart(rows: list[dict[str, Any]], x_key: str, y_key: str, title: str, invert: bool = False) -> str:
    if len(rows) < 2:
        return f"<div class=\"chart\"><p class=\"muted\">{_esc(title)} 데이터 부족</p></div>"
    values = [_float(row.get(y_key)) for row in rows]
    lo, hi = min(values), max(values)
    if lo == hi:
        hi = lo + 1.0
    points = []
    width, height, pad = 720, 220, 26
    for idx, value in enumerate(values):
        x = pad + idx * ((width - pad * 2) / max(1, len(values) - 1))
        ratio = (value - lo) / (hi - lo)
        y = pad + ratio * (height - pad * 2) if invert else height - pad - ratio * (height - pad * 2)
        points.append(f"{x:.1f},{y:.1f}")
    color = "#b42318" if invert else "#155eef"
    return f"""<div class="chart"><svg viewBox="0 0 {width} {height}" width="100%" height="220" role="img" aria-label="{_esc(title)}">
<text x="18" y="22" font-size="14" fill="#344054">{_esc(title)}</text>
<polyline points="{' '.join(points)}" fill="none" stroke="{color}" stroke-width="3"/>
<text x="18" y="{height-8}" font-size="12" fill="#667085">{_esc(str(rows[0].get(x_key)))}</text>
<text x="{width-130}" y="{height-8}" font-size="12" fill="#667085">{_esc(str(rows[-1].get(x_key)))}</text>
</svg></div>"""


def _bar_chart(rows: list[dict[str, Any]], x_key: str, y_key: str, title: str) -> str:
    if not rows:
        return f"<div class=\"chart\"><p class=\"muted\">{_esc(title)} 데이터 부족</p></div>"
    width, height, pad = 720, 220, 28
    values = [_float(row.get(y_key)) for row in rows]
    max_abs = max(abs(value) for value in values) or 1.0
    bar_w = (width - pad * 2) / len(rows) * 0.62
    zero_y = height / 2
    bars = []
    for idx, row in enumerate(rows):
        value = _float(row.get(y_key))
        x = pad + idx * ((width - pad * 2) / len(rows)) + bar_w * 0.25
        h = abs(value) / max_abs * (height / 2 - pad)
        y = zero_y - h if value >= 0 else zero_y
        color = "#047857" if value >= 0 else "#b42318"
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{color}"/><text x="{x:.1f}" y="{height-8}" font-size="10" fill="#667085">{_esc(str(row.get(x_key)))}</text>')
    return f"""<div class="chart"><svg viewBox="0 0 {width} {height}" width="100%" height="220" role="img" aria-label="{_esc(title)}">
<text x="18" y="22" font-size="14" fill="#344054">{_esc(title)}</text>
<line x1="{pad}" x2="{width-pad}" y1="{zero_y}" y2="{zero_y}" stroke="#d8dee8"/>
{''.join(bars)}
</svg></div>"""


def _metric(label: str, value: str) -> str:
    return f"<div class=\"metric\"><span>{_esc(label)}</span><strong>{value}</strong></div>"


def _label(key: str) -> str:
    labels = {
        "period": "기간",
        "date": "일자",
        "days": "일수",
        "trade_count": "거래 수",
        "wins": "승리",
        "win_rate": "승률",
        "start_equity_krw": "시작 자산",
        "end_equity_krw": "종료 자산",
        "final_equity_krw": "최종 자산",
        "pnl_krw": "손익",
        "return_pct": "수익률",
        "total_return_pct": "수익률",
        "drawdown_pct": "하락률",
        "mdd_pct": "최대 하락률",
        "max_drawdown_pct": "최대 하락률",
        "scenario": "시나리오",
        "strategy": "전략",
        "plan": "플랜",
        "profit_factor": "PF",
        "decision": "판정",
        "market_state": "시장 상태",
        "status": "상태",
        "active_route": "활성 Route",
        "candidate_route": "후보 Route",
        "backfill_start": "Backfill 시작",
        "server_ready": "서버 준비",
        "manual_switch_required": "수동 전환 필요",
        "ROLLING_ONLY_CONTROL": "Rolling",
        "ROLLING_ONLY_DOMINANCE_OVERLAY": "Rolling+Dom",
        "BALANCED_ONLY_CONTROL": "Balanced",
        "BALANCED_ONLY_DOMINANCE_OVERLAY": "Balanced+Dom",
        "POLICY_BLEND_CONTROL": "Blend",
        "POLICY_BLEND_DOMINANCE_OVERLAY": "Blend+Dom",
        "SCENARIO_AGENT_ROUTER_V1": "Router",
    }
    return labels.get(key, key)


def _display(value: Any, key: str) -> str:
    if value is None:
        return "N/A"
    if key.endswith("_krw") or key in {"pnl_krw"}:
        return _money(value)
    if key.endswith("_pct") or key in {"win_rate"} or key.isupper():
        pct_value = value * 100 if key == "win_rate" and abs(_float(value)) <= 1 else value
        return _pct(pct_value)
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "예" if value else "아니오"
    return _esc(value)


def _json_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str).replace("<", "\\u003c")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.0f}원"
    except (TypeError, ValueError):
        return "N/A"


def _pct(value: Any) -> str:
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def _num(value: Any) -> str:
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return "N/A"


def _bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)
