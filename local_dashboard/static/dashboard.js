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
  return recordsView(records, true, account);
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
    section("월단위 투자기록", "월을 클릭하면 같은 월에 속한 주/일 기록이 아래에 표시됩니다. 최신 월이 위입니다.", table(months, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], compact ? 24 : 200, "month-table")),
    section(`${month || "선택 월"} 주단위 기록`, "선택한 월 안에서 주별 손익과 낙폭을 봅니다.", table(weeks, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], compact ? 12 : 200)),
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
