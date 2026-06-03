const state = { view: "overview", data: {}, selectedMonth: null };

const endpoints = {
  overview: "/api/investment-records",
  records: "/api/investment-records",
  logs: "/api/investment-logs",
  scenarios: "/api/investment-records",
  improvement: "/api/v690-dashboard",
  vwap: "/api/v691-dashboard",
  research: "/api/v688-dashboard",
};

const labels = {
  period: "기간",
  time: "일시",
  market: "코인",
  route_label: "시나리오",
  scenario_label: "시나리오",
  route_status: "상태",
  result: "결과",
  trade_comment: "코멘트",
  start_equity_krw: "시작금",
  end_equity_krw: "종료금",
  final_equity_krw: "최종금",
  pnl_krw: "손익",
  realized_pnl_krw: "실현손익",
  return_pct: "수익률",
  mdd_pct: "최대낙폭",
  profit_factor: "PF",
  trade_count: "거래수",
  candidate_count: "후보수",
  enter_count: "진입",
  wait_count: "대기",
  primary_block_reason: "대기 사유",
  action: "행동",
  reason: "근거",
  source_mode: "자료",
  decision: "판정",
  recommended_primary_label: "추천 운용",
  current_active_route: "현재 active",
  investment_start_date: "투자 시작일",
  scenario: "시나리오",
  score: "종합점수",
  eligible_for_operation: "운용후보",
  exclusion_reason: "제외 사유",
  active_change_applied: "자동변경",
  live_order_allowed: "실거래",
  shadow_candidates: "Shadow 후보",
  research_only: "연구 후보",
  baseline_still_best: "기존 유지",
  fix_target: "보완 대상",
  key_rule: "핵심 규칙",
  rule: "규칙",
  risk: "위험",
  feature: "Feature",
  test_status: "검증 상태",
  full_return_pct: "전체 수익률",
  full_mdd_pct: "전체 MDD",
  overfit_risk: "과최적화",
  bold_research: "과감 연구",
  experiment_type: "실험 유형",
  boldness_level: "과감도",
  risk_profile: "위험 성격",
  return_delta_vs_lgm3_pct: "LG-M3 대비 수익",
  mdd_delta_vs_lgm3_pct: "LG-M3 대비 MDD",
  vwap_shadow_candidates: "VWAP Shadow",
  vwap_research_only: "VWAP 연구",
  drawdown_shadow_candidates: "낙폭 후보",
  drawdown_reduction_pct: "낙폭 개선",
  drawdown_reduction_ratio: "낙폭 개선율",
  drawdown_tradeoff_score: "낙폭/수익 균형",
  saved_loss: "방어 손실",
  missed_profit: "놓친 수익",
  net_effect: "순효과",
  hwm_giveback: "HWM 반납",
  false_skip_count: "과잉 차단",
  false_entry_count: "오진입 감소",
  average_expected_rr: "예상 손익비",
  average_realized_rr: "실현 손익비",
  best_market_state: "강한 시장",
  worst_market_state: "약한 시장",
  event_count: "이벤트",
  drawdown_reduction_score: "낙폭 방어점수",
};

const money = (value) => `${Number(value || 0).toLocaleString("ko-KR", { maximumFractionDigits: 0 })} KRW`;
const pct = (value) => `${Number(value || 0).toFixed(2)}%`;
const signedMoney = (value) => {
  const number = Number(value || 0);
  return `${number > 0 ? "+" : ""}${number.toLocaleString("ko-KR", { maximumFractionDigits: 0 })} KRW`;
};

async function load() {
  const endpoint = endpoints[state.view] || endpoints.overview;
  const [health, account, records, payload] = await Promise.all([
    fetch("/api/health").then((r) => r.json()),
    fetch("/api/account").then((r) => r.json()),
    fetch("/api/investment-records").then((r) => r.json()),
    fetch(endpoint).then((r) => r.json()),
  ]);
  state.data = {
    health: health.data || {},
    account: account.data || {},
    records: records.data || {},
    payload: payload.data || {},
  };
  render();
}

function render() {
  const { health, account, records, payload } = state.data;
  const safe = !health.live_order_allowed && !health.real_order_enabled && !health.auto_apply_allowed;
  document.querySelector("#status").textContent = safe ? "PAPER 전용 / 실거래 차단" : "실거래 설정 점검 필요";
  document.querySelector("#status").className = safe ? "status" : "status danger";
  document.querySelector("#cards").innerHTML = topCards(records, account);
  document.querySelector("#view-title").textContent = title(state.view);
  document.querySelector("#content").innerHTML = content(state.view, payload, account, records);
  bindRenderedEvents();
}

function topCards(records, account) {
  const operating = records.operating_summary || {};
  const latestMonth = (records.monthly || [])[0] || {};
  return [
    card("추천 운용 시나리오", operating.recommended_primary_label || records.scenario_policy?.primary_route_label || "-"),
    card("오늘 기록", records.latest_record_date || "-", records.record_staleness?.status === "STALE" ? "danger" : "ok"),
    card("계좌 평가", money(account.current_equity_krw || latestMonth.end_equity_krw || records.initial_cash_krw || 0)),
    card("이번달 손익", signedMoney(operating.this_month?.pnl_krw ?? latestMonth.pnl_krw ?? 0), Number(operating.this_month?.pnl_krw ?? latestMonth.pnl_krw ?? 0) >= 0 ? "ok" : "danger"),
  ].join("");
}

function title(view) {
  return {
    overview: "투자 현황",
    records: "월/주/일 기록",
    logs: "매매/판단 로그",
    scenarios: "시나리오 결론",
    improvement: "개선 루프",
    vwap: "VWAP/낙폭 검증",
    research: "연구 보관",
  }[view] || "투자 현황";
}

function content(view, data, account, records) {
  if (view === "overview") return overviewView(records, account);
  if (view === "records") return recordsView(records);
  if (view === "logs") return logsView(data);
  if (view === "scenarios") return scenariosView(records);
  if (view === "improvement") return improvementView(data);
  if (view === "vwap") return vwapView(data);
  if (view === "research") return researchView(data);
  return overviewView(records, account);
}

function overviewView(records) {
  const operating = records.operating_summary || {};
  const conclusion = records.plain_conclusion || {};
  const today = operating.today || latestRow(records.daily || []);
  const week = operating.this_week || latestRow(records.weekly || []);
  const month = operating.this_month || latestRow(records.monthly || []);
  return [
    notice("현재 결론", conclusion.current_operation_conclusion || "검증 산출물이 아직 없습니다."),
    section("오늘 / 이번주 / 이번달", "매일 확인할 핵심 숫자입니다.", table([
      { period: today.period || records.latest_record_date, route_label: operating.recommended_primary_label, pnl_krw: today.pnl_krw, return_pct: today.return_pct, trade_count: today.trade_count, end_equity_krw: today.end_equity_krw },
      { period: week.period, route_label: operating.recommended_primary_label, pnl_krw: week.pnl_krw, return_pct: week.return_pct, trade_count: week.trade_count },
      { period: month.period, route_label: operating.recommended_primary_label, pnl_krw: month.pnl_krw, return_pct: month.return_pct, trade_count: month.trade_count },
    ], ["period", "route_label", "pnl_krw", "return_pct", "trade_count", "end_equity_krw"], 5)),
    section("운용 상태", "자동 변경 없이 paper 기준으로만 표시합니다.", table([{
      investment_start_date: operating.investment_start_date || records.start_date,
      recommended_primary_label: operating.recommended_primary_label,
      current_active_route: operating.current_active_route,
      active_change_applied: false,
      live_order_allowed: false,
    }], ["investment_start_date", "recommended_primary_label", "current_active_route", "active_change_applied", "live_order_allowed"], 5)),
    section("최근 월간 흐름", "최근 월이 위에 옵니다.", table(records.monthly || [], ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], 6)),
  ].join("");
}

function recordsView(records) {
  const months = records.monthly || [];
  if (!state.selectedMonth && months.length) state.selectedMonth = months[0].period;
  const month = state.selectedMonth || months[0]?.period;
  const weeks = (records.weekly || []).filter((row) => row.month === month);
  const days = (records.daily || []).filter((row) => row.month === month);
  return [
    section("월 기록", "월을 클릭하면 해당 월의 주/일 기록만 아래에 표시됩니다.", table(months, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "candidate_count", "wait_count", "result", "trade_comment"], 120, "month-table")),
    section(`${month || "선택 월"} 주 기록`, "선택한 월의 주간 기록입니다.", table(weeks, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "candidate_count", "wait_count", "result", "trade_comment"], 80)),
    section(`${month || "선택 월"} 일 기록`, "거래가 없는 날은 거래없음과 이유를 표시합니다.", table(days, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result", "trade_comment"], 200)),
  ].join("");
}

function logsView(data) {
  return [
    section("Forward 후보 로그", "최근 forward paper 후보와 대기 사유입니다.", table(data.forward_candidate_logs || [], ["time", "market", "strategy_id", "entry_decision", "result", "primary_block_reason", "trade_comment"], 200)),
    section("매수/매도 기록", "paper 체결 로그입니다.", table(data.trade_logs || [], ["time", "market", "action", "route_label", "size_krw", "realized_pnl_krw", "pnl_pct", "reason"], 300)),
    section("시나리오 판단 기록", "각 시점의 적용 판단 근거입니다.", table(data.scenario_logs || [], ["time", "market", "route_label", "market_state", "action", "guard_on", "dominance_risk", "reason"], 300)),
  ].join("");
}

function scenariosView(records) {
  const decision = records.scenario_decision || {};
  const conclusion = decision.conclusion || {};
  return [
    notice("2022~현재 재검증 결론", conclusion.answer_to_user_question || "-"),
    section("운용 결론", "", table([
      { decision: "장기 결론", reason: conclusion.long_term_conclusion },
      { decision: "2026 결론", reason: conclusion.current_operation_conclusion },
      { decision: "업그레이드 후보", reason: conclusion.new_or_upgraded_scenario },
      { decision: "연구 보관", reason: conclusion.not_promoted },
    ], ["decision", "reason"], 10)),
    section("2026 운용 후보 순위", "표본이 부족한 연구 시나리오는 아래로 내립니다.", table(decision.current_rows || [], ["scenario", "source", "eligible_for_operation", "exclusion_reason", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count", "score", "decision"], 30)),
    section("2022~현재 장기 검증 순위", "장기 복리 성과와 손실 방어를 함께 봅니다.", table(decision.long_term_rows || [], ["scenario", "source", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count", "score", "decision"], 30)),
  ].join("");
}

function improvementView(data) {
  const decision = data.decision || {};
  const loop = data.loop || {};
  const review = data.llm_review || {};
  return [
    notice("V6.9.0 개선 루프 결론", `최종 판정: ${decision.decision || loop.decision || "-"} / active 자동변경 없음 / 실거래 없음`),
    section("최종 후보 판정", "통과한 개선안도 shadow 후보로만 둡니다.", table([{
      shadow_candidates: (decision.shadow_candidates || []).join(", "),
      research_only: (decision.research_only || []).join(", "),
      bold_research: (decision.bold_research || []).join(", "),
      baseline_still_best: decision.baseline_still_best,
      active_change_applied: false,
      live_order_allowed: false,
    }], ["shadow_candidates", "research_only", "bold_research", "baseline_still_best", "active_change_applied", "live_order_allowed"], 5)),
    section("개선 후보", "실패 패턴에서 생성된 개선 가설입니다.", table(data.candidates?.candidates || [], ["scenario", "base", "fix_target", "key_rule", "risk", "evidence_count", "test_status"], 20)),
    section("2026 개선 검증", "LG-M3 기준 개선 규칙의 shadow 검증 결과입니다.", table(data.backtest_2026?.rows || [], ["scenario", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count", "profit_giveback_3d", "net_effect", "decision"], 20)),
    section("과감한 연구 시도", "운용 승격용이 아니라 수익률과 낙폭이 크게 벌어지는 연구 후보입니다.", table((data.backtest_2026?.rows || []).filter((row) => row.experiment_type === "BOLD_RESEARCH"), ["scenario", "boldness_level", "risk_profile", "return_pct", "mdd_pct", "profit_factor", "return_delta_vs_lgm3_pct", "mdd_delta_vs_lgm3_pct", "decision"], 20)),
    section("전체기간 안전성", "2026에서 좋아 보여도 전체기간에서 버티는지 확인합니다.", table(data.full_period_safety?.rows || [], ["scenario", "full_return_pct", "full_mdd_pct", "2026_return_pct", "2026_mdd_pct", "overfit_risk", "decision"], 20)),
    section("LLM 복기", "LLM은 계산하지 않고 엔진 산출물을 요약합니다.", table([review], ["llm_used", "fallback_used", "key_findings", "recommended_experiments", "active_change_applied", "manual_review_required"], 5)),
  ].join("");
}

function vwapView(data) {
  const decision = data.decision || {};
  const review = data.llm_review || {};
  return [
    notice("V6.9.1 VWAP/VPF + 낙폭 축소 결론", `판정: ${decision.decision || "-"} / VWAP는 shadow/research 전용 / active 자동변경 없음`),
    section("최종 후보", "낙폭 축소와 missed profit 균형을 통과한 후보만 shadow 관찰 후보입니다.", table([{
      vwap_shadow_candidates: (decision.vwap_shadow_candidates || []).join(", "),
      drawdown_shadow_candidates: (decision.drawdown_shadow_candidates || []).join(", "),
      vwap_research_only: (decision.vwap_research_only || []).join(", "),
      baseline_still_best: decision.baseline_still_best,
      active_change_applied: false,
      live_order_allowed: false,
    }], ["vwap_shadow_candidates", "drawdown_shadow_candidates", "vwap_research_only", "baseline_still_best", "active_change_applied", "live_order_allowed"], 5)),
    section("Feature 효과성", "VWAP/VPF가 손실 차단, follow-through, 반납 축소에 도움이 되는지 본 표입니다.", table(data.effectiveness?.rows || [], ["feature", "event_count", "return_after_1h", "return_after_4h", "return_after_1d", "saved_loss", "missed_profit", "net_effect", "drawdown_reduction_score", "decision"], 20)),
    section("2026 VWAP 시나리오 검증", "수익률뿐 아니라 MDD, 손익비, saved loss, missed profit을 함께 봅니다.", table(data.backtest_2026?.rows || [], ["scenario", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "return_mdd_ratio", "saved_loss", "missed_profit", "net_effect", "decision"], 20)),
    section("낙폭 축소 분석", "MDD 개선폭이 수익률 희생과 missed profit보다 큰지 확인합니다.", table(data.drawdown?.rows || [], ["scenario", "mdd_pct", "mdd_delta_vs_lgm3_pct", "drawdown_reduction_ratio", "saved_loss", "missed_profit", "net_effect", "return_delta_vs_lgm3_pct", "drawdown_tradeoff_score", "decision"], 20)),
    section("전체기간 안전성", "2026 개선 후보가 전체기간에서도 과최적화가 아닌지 확인합니다.", table(data.full_period_safety?.rows || [], ["scenario", "full_return_pct", "full_mdd_pct", "2026_return_pct", "2026_mdd_pct", "missed_profit", "overfit_risk", "decision"], 20)),
    section("LLM 복기", "계산 결과를 요약한 fallback 리뷰입니다.", table([review], ["llm_used", "fallback_used", "key_findings", "drawdown_best", "recommended_experiments", "active_change_applied", "manual_review_required"], 5)),
  ].join("");
}

function researchView(data) {
  return [
    notice("연구 보관", "운용 판단에 바로 필요한 자료가 아니므로 별도 탭에 보관합니다."),
    section("V6.8.8 변동분석", "자동 적용 없이 수동 검토용 경고만 남깁니다.", table(data.active_analysis?.recommendations || [], ["recommendation_id", "trigger_type", "severity", "confidence", "expected_benefit", "allowed_action", "manual_approval_required"], 80)),
    section("판단차이", "사후 결과가 부족하면 UNKNOWN으로 유지합니다.", table(data.disagreement?.rows || [], ["timestamp", "market", "active_decision", "best_decision_ex_post", "disagreement_type", "lesson"], 80)),
    section("수익 반납", "수익 후 1/3/5일 반납률입니다.", table(data.profit_giveback?.rows || [], ["scenario_id", "profit_date", "profit_day_pnl", "giveback_ratio_1d", "giveback_ratio_3d", "giveback_ratio_5d", "recommendation"], 80)),
  ].join("");
}

function latestRow(rows) {
  return rows.find((row) => row && row.period) || {};
}

function card(label, value, tone = "") {
  return `<div class="metric"><div class="label">${label}</div><div class="value ${tone}">${escapeHtml(value ?? "-")}</div></div>`;
}

function notice(titleText, body) {
  return `<section class="notice"><strong>${escapeHtml(titleText)}</strong><p>${escapeHtml(body || "-")}</p></section>`;
}

function section(titleText, note, body) {
  return `<section class="data-section"><div class="section-head"><h3>${escapeHtml(titleText)}</h3>${note ? `<p>${escapeHtml(note)}</p>` : ""}</div>${body}</section>`;
}

function table(rows, keys, limit = 100, className = "") {
  const clean = (rows || []).filter((row) => row && Object.keys(row).length);
  if (!clean.length) return `<p class="empty">표시할 데이터 없음</p>`;
  const body = clean.slice(0, limit).map((row) => {
    const monthAttr = row.kind === "monthly" ? ` data-month="${escapeHtml(row.period)}"` : "";
    const classes = [
      row.kind === "monthly" && row.period === state.selectedMonth ? "selected" : "",
      row.comparison_rank === "best" ? "best-row" : "",
      row.comparison_rank === "worst" ? "worst-row" : "",
    ].filter(Boolean).join(" ");
    return `<tr${monthAttr} class="${classes}">${keys.map((key) => `<td class="${tone(key, row[key])}">${fmt(key, row[key])}</td>`).join("")}</tr>`;
  }).join("");
  return `<div class="wrap ${className}"><table><thead><tr>${keys.map((key) => `<th>${labels[key] || key}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function fmt(key, value) {
  if (value === undefined || value === null || value === "") return "-";
  if (Array.isArray(value)) return escapeHtml(value.join(", "));
  if (key.includes("krw") || key.includes("equity")) return escapeHtml(money(value));
  if (key.includes("pct") || key.includes("return") || key.includes("mdd") || key.includes("ratio")) return escapeHtml(pct(value));
  if (key === "score" || key.includes("score") || key.includes("rr")) return Number(value || 0).toFixed(2);
  if (typeof value === "boolean") return value ? "예" : "아니오";
  return escapeHtml(String(value));
}

function tone(key, value) {
  if (["pnl_krw", "realized_pnl_krw", "return_pct", "pnl_pct", "net_effect", "return_delta_vs_lgm3_pct"].includes(key)) {
    const number = Number(value || 0);
    return number > 0 ? "ok" : number < 0 ? "danger" : "";
  }
  if (key === "mdd_pct") return Number(value || 0) < -10 ? "danger" : "";
  if (key === "mdd_delta_vs_lgm3_pct" || key === "drawdown_reduction_pct") return Number(value || 0) > 0 ? "ok" : "danger";
  if (key === "live_order_allowed" || key === "active_change_applied") return value ? "danger" : "ok";
  return "";
}

function bindRenderedEvents() {
  document.querySelectorAll("[data-month]").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedMonth = row.dataset.month;
      render();
    });
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

document.querySelectorAll(".side button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".side button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.view = button.dataset.view;
    load();
  });
});
document.querySelector("#refresh").addEventListener("click", load);
load();
setInterval(load, 10000);
