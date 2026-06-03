const state = { view: "overview", data: {}, selectedMonth: null };

const endpoints = {
  overview: "/api/investment-records",
  records: "/api/investment-records",
  trades: "/api/investment-logs",
  decisions: "/api/investment-logs",
  routes: "/api/investment-records",
  validation: "/api/pattern-validation",
  risk: "/api/atr-research",
  control: "/api/control-tower",
  v688Telemetry: "/api/v688-dashboard",
  v688Disagreement: "/api/v688-dashboard",
  v688Active: "/api/v688-dashboard",
  v688LLM: "/api/v688-dashboard",
};

const labels = {
  period: "기간",
  route_id: "시나리오",
  route_label: "약칭",
  route_status: "상태",
  scenario: "시나리오",
  scenario_label: "약칭",
  market: "코인",
  action: "행동",
  time: "일시",
  result: "결과",
  trade_comment: "코멘트",
  trade_count: "거래수",
  skipped_trade_count: "스킵",
  start_equity_krw: "시작금",
  end_equity_krw: "종료금",
  final_equity_krw: "최종금",
  pnl_krw: "손익",
  realized_pnl_krw: "실현손익",
  return_pct: "수익률",
  pnl_pct: "거래수익률",
  mdd_pct: "최대낙폭",
  size_krw: "투입금",
  reason: "근거",
  source_mode: "자료",
  decision: "판정",
  profit_factor: "PF",
  win_rate_pct: "승률",
  market_state: "시장상태",
  selected_agent: "적용 에이전트",
  guard_on: "가드",
  hard_guard: "하드가드",
  dominance_risk: "도미넌스 위험",
  month_return_pct: "월간흐름",
  hwm_drawdown_pct: "고점대비",
  live_order_allowed: "실거래허용",
  auto_apply_allowed: "자동적용",
  comparison_rank: "월별구분",
  threshold_hwm_drawdown_pct: "낙폭기준",
  action_when_breached: "대응",
  total_pnl_krw: "총손익",
  avg_win_loss_ratio: "손익비",
  expectancy_krw: "기대손익",
  pattern: "패턴",
  surge_rate_pct: "급등비율",
  surge_count: "급등수",
  recommended_route: "추천",
  return_delta_pct: "수익률 차이",
  mdd_delta_pct: "MDD 차이",
  investment_start_date: "투자 시작",
  primary_route_label: "주 시나리오",
  previous_primary_route_label: "이전 주 시나리오",
  candidate: "후보",
  beats_active_return: "수익 우위",
  beats_or_matches_active_mdd: "낙폭 우위",
  trade_count_ok: "표본 충분",
  lookahead_clean: "룩어헤드 없음",
  session_id: "세션",
  candidate_index: "순번",
  candidate_count: "후보수",
  enter_count: "진입수",
  wait_count: "대기수",
  strategy_id: "전략",
  entry_decision: "진입판단",
  primary_block_reason: "대기/차단 사유",
  trade_event_count: "체결틱",
  orderbook_event_count: "호가틱",
  orderbook_available: "호가확인",
  scenario_id: "시나리오",
  display_name: "이름",
  scenario_family: "계열",
  preferred_market_states: "유리한 시장",
  weak_market_states: "약한 시장",
  candidates_seen: "후보",
  skip_count: "스킵",
  realized_pnl_krw: "실현손익",
  daily_return_pct: "일수익률",
  recommendation_id: "추천ID",
  trigger_type: "트리거",
  severity: "강도",
  confidence: "확신도",
  expected_benefit: "기대효과",
  allowed_action: "허용동작",
  manual_approval_required: "수동검토",
  disagreement_type: "판단차이",
  active_decision: "Active 판단",
  best_decision_ex_post: "사후 최선",
  lesson: "교훈",
  profit_day_pnl: "수익일 손익",
  giveback_ratio_1d: "1일 반납률",
  giveback_ratio_3d: "3일 반납률",
  giveback_ratio_5d: "5일 반납률",
  Recommendation: "추천",
  Variable: "변수",
  sample_count: "표본수",
  llm_used: "LLM 사용",
  fallback_used: "Fallback",
  summary: "요약",
};

const money = (value) => Number(value || 0).toLocaleString("ko-KR", { maximumFractionDigits: 0 }) + " KRW";
const pct = (value) => Number(value || 0).toFixed(2) + "%";
const signedMoney = (value) => {
  const number = Number(value || 0);
  const sign = number > 0 ? "+" : "";
  return sign + number.toLocaleString("ko-KR", { maximumFractionDigits: 0 }) + " KRW";
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
  const stale = records.record_staleness || {};
  const latest = records.latest_record_date || "-";
  const forward = records.latest_forward_ws || {};
  const policy = records.scenario_policy || {};
  document.querySelector("#status").textContent = safe ? "PAPER 전용 / 실거래 차단" : "실거래 설정 점검 필요";
  document.querySelector("#status").className = safe ? "status" : "status danger";
  document.querySelector("#cards").innerHTML = [
    card("주 시나리오", policy.primary_route_label || account.active_route || records.active_route || "N/A"),
    card("현재 기록일", latest, stale.status === "STALE" ? "danger" : "ok"),
    card("계좌 평가", money(account.current_equity_krw || records.initial_cash_krw || 0)),
    card("Forward 관찰", `${forward.status || "NO_DATA"} / 후보 ${forward.candidate_count ?? 0}`),
  ].join("");
  document.querySelector("#view-title").textContent = title(state.view);
  document.querySelector("#content").innerHTML = content(state.view, payload, account, records);
  bindRenderedEvents();
}

function card(label, value, tone = "") {
  return `<div class="metric"><div class="label">${label}</div><div class="value ${tone}">${escapeHtml(value ?? "N/A")}</div></div>`;
}

function title(view) {
  return {
    overview: "투자 현황판",
    records: "월/주/일 투자기록",
    trades: "매수/매도 로그",
    decisions: "시나리오 판단 로그",
    routes: "시나리오 비교",
    validation: "급등/손익비/2월 검증",
    risk: "하락장 방어 / ATR",
    control: "관제 요약",
    v688Telemetry: "V6.8.8 시나리오 계측",
    v688Disagreement: "V6.8.8 판단차이",
    v688Active: "V6.8.8 능동분석",
    v688LLM: "V6.8.8 LLM 복기",
  }[view] || "투자 현황판";
}

function content(view, data, account, records) {
  if (view === "overview") return recordsView(data, true, account);
  if (view === "records") return recordsView(data, false, account);
  if (view === "trades") {
    return [
      section("오늘 Forward 일지", "06-02 같은 실시간 paper 후보 로그입니다. 진입 조건이 약하면 거래없음으로 남깁니다.", table(data.forward_daily_calendar || [], ["period", "time", "route_label", "candidate_count", "enter_count", "wait_count", "result", "primary_block_reason", "trade_comment", "source_mode"], 30)),
      section("오늘 Forward 후보/투자로그", "실시간 후보별 코인, 전략, 진입 판단, 대기 사유입니다. 실제 주문은 차단된 paper 기록입니다.", table(data.forward_candidate_logs || [], ["time", "market", "strategy_id", "action", "result", "primary_block_reason", "trade_event_count", "orderbook_event_count", "trade_comment"], 500)),
      section("일별 매매 캘린더", "없는 날짜는 거래없음으로 남기고, forward 후보가 있던 날은 후보수와 대기 사유를 함께 표시합니다.", table(data.daily_trade_calendar || [], ["period", "route_label", "trade_count", "candidate_count", "wait_count", "result", "primary_block_reason", "trade_comment", "start_equity_krw", "end_equity_krw", "pnl_krw", "source_mode"], 500)),
      section("매수/매도 기록", "실제 체결 로그입니다. 최근 로그가 위에 오도록 정렬했습니다.", table(data.trade_logs || [], ["time", "market", "action", "route_label", "route_status", "size_krw", "realized_pnl_krw", "pnl_pct", "reason", "source_mode"], 800)),
    ].join("");
  }
  if (view === "decisions") {
    return section("시나리오 적용 히스토리", "일자와 코인별로 어떤 시나리오 판단이 적용됐는지 확인합니다.", table(data.scenario_logs || [], ["time", "market", "route_label", "market_state", "selected_agent", "action", "size_krw", "guard_on", "hard_guard", "dominance_risk", "pf20", "month_return_pct", "hwm_drawdown_pct", "reason"], 800));
  }
  if (view === "routes") return routesView(data);
  if (view === "validation") return validationView(data);
  if (view === "risk") {
    return [
      section("ATR 커버리지", "", table([data.coverage || {}], ["total_atr_trades", "covered_by_1m", "covered_by_5m", "covered_by_15m", "uncovered", "best_coverage_pct", "decision"], 5)),
      section("ATR 판정", "", table([data.precision || {}], ["final_atr_decision", "reason", "shadow_candidate_allowed", "active_route_change_applied"], 5)),
    ].join("");
  }
  if (view === "control") {
    const recs = (data.recommendations || []).map((item) => ({ recommendation: item }));
    const risks = (data.risk_flags || []).map((item) => ({ risk_flag: item }));
    return [section("권고", "", table(recs, ["recommendation"], 30)), section("위험 플래그", "", table(risks, ["risk_flag"], 30))].join("");
  }
  if (view === "v688Telemetry") return v688TelemetryView(data);
  if (view === "v688Disagreement") return v688DisagreementView(data);
  if (view === "v688Active") return v688ActiveView(data);
  if (view === "v688LLM") return v688LLMView(data);
  return recordsView(records, true, account);
}

function v688TelemetryView(data) {
  return [
    section("Route State", "표시 route와 실제 paper/forward route를 분리합니다.", table([data.scenario_genome?.route_state || {}], ["display_primary_route", "actual_paper_primary_route", "forward_runner_route", "mismatch_warning"], 5)),
    section("Scenario Genome", "시나리오별 투자 카드입니다.", table(data.scenario_genome?.cards || [], ["scenario_id", "display_name", "scenario_family", "status", "preferred_market_states", "weak_market_states", "entry_style", "risk_style"], 80)),
    section("Daily Telemetry", "일별 후보/진입/손익/데이터 품질입니다.", table(data.scenario_daily?.rows || [], ["date", "scenario_id", "route_status", "market_state", "candidates_seen", "enter_count", "wait_count", "skip_count", "realized_pnl_krw", "daily_return_pct", "data_quality_flags"], 200)),
    section("Weekly Telemetry", "주별 집계입니다.", table(data.scenario_weekly?.rows || [], ["week", "scenario_id", "weekly_pnl", "weekly_return_pct", "MDD", "PF", "win_rate", "trade_count", "candidate_count", "enter_rate", "failure_signatures"], 80)),
    section("Monthly Telemetry", "월별 집계입니다.", table(data.scenario_monthly?.rows || [], ["month", "scenario_id", "monthly_pnl", "monthly_return_pct", "MDD", "PF", "trade_count", "candidate_count", "recommendation"], 80)),
  ].join("");
}

function v688DisagreementView(data) {
  return [
    section("Scenario Disagreement Matrix", "active와 shadow의 판단 차이를 기록합니다. 사후 결과가 부족하면 UNKNOWN으로 둡니다.", table(data.disagreement?.rows || [], ["event_id", "timestamp", "market", "active_decision", "best_decision_ex_post", "active_missed_profit", "active_saved_loss", "disagreement_type", "lesson"], 120)),
    section("Missed Opportunity", "후보가 있었지만 진입하지 않은 경우입니다.", table(data.missed_opportunity?.rows || [], ["event_id", "timestamp", "market", "strategy_id", "entry_decision", "primary_block_reason"], 120)),
    section("Profit Giveback", "수익 후 1/3/5일 반납률입니다.", table(data.profit_giveback?.rows || [], ["scenario_id", "profit_date", "profit_day_pnl", "next_1d_pnl", "next_3d_pnl", "next_5d_pnl", "giveback_ratio_1d", "giveback_ratio_3d", "giveback_ratio_5d", "recommendation"], 120)),
    section("Variable Convergence", "공통 변수 후보입니다. 표본 부족은 과장하지 않습니다.", table(data.variable_convergence?.winning_common_variables || [], ["Variable", "sample_count", "Win Correlation", "Loss Correlation", "False Skip", "False Entry", "Recommendation"], 80)),
  ].join("");
}

function v688ActiveView(data) {
  return [
    section("Active Analysis Recommendations", "자동 적용 없이 수동 검토 대상으로만 남깁니다.", table(data.active_analysis?.recommendations || [], ["recommendation_id", "trigger_type", "severity", "confidence", "expected_benefit", "risk_of_overfit", "data_sufficiency", "allowed_action", "manual_approval_required"], 80)),
    section("Pipeline Health", "화면 날짜와 ledger 갱신은 별도 상태입니다.", table([data.active_analysis?.pipeline_health || {}], ["status", "latest_forward_date", "candidate_count", "forward_collector_stale", "candidate_log_stale", "decision_loop_stale", "ledger_update_stale"], 5)),
    section("Candidate To Ledger", "", table([data.active_analysis?.candidate_to_ledger || {}], ["candidate_count", "forward_enter_count", "paper_trade_count", "ledger_gap", "interpretation"], 5)),
  ].join("");
}

function v688LLMView(data) {
  return [
    section("Daily Review", "원시 로그 전체가 아니라 엔진 요약 input pack 기반입니다.", table([data.llm_daily || {}], ["review_type", "period", "llm_used", "fallback_used", "summary", "active_change_applied", "live_order_allowed"], 5)),
    section("Weekly Council", "", table([data.llm_weekly || {}], ["review_type", "period", "llm_used", "fallback_used", "summary", "active_change_applied", "live_order_allowed"], 5)),
    section("Monthly Deck Review", "", table([data.llm_monthly || {}], ["review_type", "period", "llm_used", "fallback_used", "summary", "active_change_applied", "live_order_allowed"], 5)),
  ].join("");
}

function routesView(data) {
  const policy = data.scenario_policy || {};
  const feedback = policy.daily_llm_feedback || {};
  return [
    section("Route-Agent 정책", "검증된 추천만 paper 주 시나리오로 올리고, 이전 주 시나리오는 shadow로 계속 추적합니다.", table([{
      investment_start_date: policy.investment_start_date || data.start_date,
      primary_route_label: policy.primary_route_label,
      previous_primary_route_label: policy.previous_primary_route_label || "-",
      recommended_route: data.route_agent_recommendation?.recommended_route,
      reason: data.route_agent_recommendation?.reason,
      auto_apply_allowed: data.route_agent_recommendation?.auto_apply_allowed,
    }], ["investment_start_date", "primary_route_label", "previous_primary_route_label", "recommended_route", "reason", "auto_apply_allowed"], 5)),
    section("운영 유지 5개", "현재 비교 대상입니다. 새 후보가 올라오면 성적이 낮은 시나리오부터 연구 보관으로 이동합니다.", table(policy.maintained_routes || data.routes || [], ["scenario_label", "route_status", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "win_rate_pct", "trade_count", "decision"], 10)),
    section("Shadow", "주 시나리오가 아닌 운영 추적군입니다.", table(policy.shadow_routes || [], ["scenario_label", "route_status", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count"], 10)),
    section("Research 보관", "상위 5개 밖으로 밀린 시나리오입니다.", table(policy.research_routes || data.research_routes || [], ["scenario_label", "route_status", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count"], 30)),
    section("시장상황 피드백", "매일 LLM 리포트로 연결할 준비 상태입니다. 자동 적용은 막아 둡니다.", table([feedback], ["status", "planned_report", "auto_apply_allowed"], 5)),
    section("월별 변화량 비교", "초록은 해당 월 최고, 빨강은 해당 월 최저 시나리오입니다.", table(data.monthly_by_route || [], ["period", "route_label", "comparison_rank", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], 500)),
  ].join("");
}

function validationView(data) {
  const feb = data.february_feedback || {};
  const srr = data.surge_rr_scenario || {};
  return [
    section("검증 요약", "", table([{
      기간: `${data.data_range?.start || "-"} ~ ${data.data_range?.end || "-"}`,
      거래수: data.data_range?.trade_count || 0,
      판정: data.decision || "-",
      급등정의: data.surge_definition || "-",
    }], ["기간", "거래수", "급등정의", "판정"], 5)),
    section("SRR 2026 시나리오 검증", "급등+손익비 조건을 2026-01-01부터 복리 shadow로 검증했습니다. WF는 이전 기간 학습만 사용, ORACLE은 참고용입니다.", table(srr.routes || [], ["scenario_label", "source_mode", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "trade_count", "skipped_trade_count", "decision"], 20)),
    section("SRR Oracle 참고값", "전체 기간을 보고 만든 조건이라 승격 근거로 쓰지 않습니다.", table(srr.oracle_reference_routes || [], ["scenario", "source_mode", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "trade_count", "skipped_trade_count"], 20)),
    section("SRR 승격 체크", "", table([srr.promotion_check || {}], ["candidate", "beats_active_return", "beats_or_matches_active_mdd", "trade_count_ok", "lookahead_clean", "auto_apply_allowed"], 5)),
    section("급등 조건 후보", "pnl_pct 0.50% 이상 거래가 많이 나온 조건입니다.", table(data.surge_patterns || [], ["pattern", "trade_count", "surge_count", "surge_rate_pct", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "expectancy_krw", "interpretation"], 30)),
    section("손익비 패턴", "손익비 = 평균 이익 / 평균 손실, PF = 총이익 / 총손실입니다.", table(data.risk_reward_patterns || [], ["pattern", "trade_count", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "expectancy_krw", "max_drawdown_pct"], 30)),
    section("2월 실패 피드백", "", table(feb.route_monthly_rank || [], ["route_id", "period", "return_pct", "mdd_pct", "trade_count"], 20)),
    section("2월 손실 원인", "", table((feb.insights || []).map((item) => ({ insight: item })), ["insight"], 20)),
    section("낙폭 차단 sweep", "고점대비 낙폭 기준 도달 시 skip 또는 35% 축소를 넣은 사후검증입니다.", table(data.drawdown_cut_sweep || [], ["threshold_hwm_drawdown_pct", "action_when_breached", "total_pnl_krw", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "max_drawdown_pct"], 20)),
  ].join("");
}

function recordsView(data, compact, account) {
  const months = data.monthly || [];
  if (!state.selectedMonth && months.length) state.selectedMonth = months[0].period;
  const month = state.selectedMonth || months[0]?.period;
  const weeks = (data.weekly || []).filter((row) => row.month === month);
  const days = (data.daily || []).filter((row) => row.month === month);
  return [
    statusBoard(data, account || {}),
    section("월단위 투자기록", "월을 클릭하면 같은 월에 속한 주/일 기록이 아래에 표시됩니다. 최신 월이 위입니다.", table(months, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "candidate_count", "wait_count", "result", "trade_comment"], compact ? 24 : 200, "month-table")),
    section(`${month || "선택 월"} 주단위 기록`, "선택한 월 안에서 주별 손익과 낙폭을 봅니다.", table(weeks, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "candidate_count", "wait_count", "result", "trade_comment"], compact ? 12 : 200)),
    section(`${month || "선택 월"} 일단위 기록`, "거래가 없는 날짜도 거래없음으로 표시합니다.", table(days, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result", "trade_comment"], compact ? 40 : 400)),
  ].join("");
}

function statusBoard(data, account) {
  const policy = data.scenario_policy || {};
  const stale = data.record_staleness || {};
  const market = data.latest_market_data || {};
  const forward = data.latest_forward_ws || {};
  const monthRows = data.monthly || [];
  const latestMonth = monthRows[0] || {};
  return `
    <div class="status-board">
      <div>
        <div class="board-label">고정 투자 시작</div>
        <div class="board-value">${escapeHtml(policy.investment_start_date || data.start_date || "2026-01-01")}</div>
      </div>
      <div>
        <div class="board-label">주 시나리오</div>
        <div class="board-value">${escapeHtml(policy.primary_route_label || data.active_route || "-")}</div>
      </div>
      <div>
        <div class="board-label">계좌 평가</div>
        <div class="board-value">${escapeHtml(money(account.current_equity_krw || latestMonth.end_equity_krw || data.initial_cash_krw || 0))}</div>
      </div>
      <div>
        <div class="board-label">최근 월 손익</div>
        <div class="board-value ${Number(latestMonth.pnl_krw || 0) >= 0 ? "ok" : "danger"}">${escapeHtml(signedMoney(latestMonth.pnl_krw || 0))}</div>
      </div>
      <div>
        <div class="board-label">기록 상태</div>
        <div class="board-value ${stale.status === "STALE" ? "danger" : "ok"}">${escapeHtml(data.latest_record_date || "-")}</div>
      </div>
      <div>
        <div class="board-label">시장 데이터</div>
        <div class="board-value">${escapeHtml(market.latest_time || "-")}</div>
      </div>
      <div>
        <div class="board-label">Forward</div>
        <div class="board-value">${escapeHtml(forward.status || "-")}</div>
      </div>
      <div>
        <div class="board-label">실거래</div>
        <div class="board-value ok">차단</div>
      </div>
    </div>
    ${sparkline(monthRows)}
    <div class="toolbar">
      <div><b>현재 정책:</b> 주 시나리오 1개 + shadow 추적 + research 보관. 더 나은 시나리오 검증 시 2026-01-01 기준으로 재검증 후 주 시나리오 교체.</div>
      <div class="hint">최신 기록 우선</div>
    </div>`;
}

function sparkline(rows) {
  const sample = rows.slice(0, 12).reverse();
  if (!sample.length) return "";
  const maxAbs = Math.max(...sample.map((row) => Math.abs(Number(row.return_pct || 0))), 1);
  const bars = sample.map((row) => {
    const value = Number(row.return_pct || 0);
    const height = Math.max(8, Math.round((Math.abs(value) / maxAbs) * 70));
    const cls = value >= 0 ? "bar ok-bg" : "bar danger-bg";
    return `<div class="bar-cell" title="${escapeHtml(row.period)} ${pct(value)}"><div class="${cls}" style="height:${height}px"></div><span>${escapeHtml(String(row.period || "").slice(5))}</span></div>`;
  }).join("");
  return `<div class="sparkline">${bars}</div>`;
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
  if (key === "comparison_rank") return value === "best" ? "최고" : value === "worst" ? "최저" : "-";
  if (key.includes("krw") || key.includes("equity")) return escapeHtml(money(value));
  if (key.includes("pct") || key.includes("return") || key.includes("mdd") || key.includes("coverage") || key === "win_rate_pct") return escapeHtml(pct(value));
  if (typeof value === "boolean") return value ? "예" : "아니오";
  return escapeHtml(String(value));
}

function tone(key, value) {
  if (["pnl_krw", "realized_pnl_krw", "return_pct", "pnl_pct", "return_delta_pct"].includes(key)) {
    const number = Number(value || 0);
    return number > 0 ? "ok" : number < 0 ? "danger" : "";
  }
  if (key === "mdd_pct" || key === "hwm_drawdown_pct") return Number(value || 0) < -10 ? "danger" : "";
  if (key === "live_order_allowed" || key === "auto_apply_allowed") return value ? "danger" : "ok";
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
