const state = { view: "overview", data: {}, selectedMonth: null };

const endpoints = {
  overview: "/api/investment-records",
  records: "/api/investment-records",
  logs: "/api/investment-logs",
  scenarios: "/api/investment-records",
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
};

const money = (value) => Number(value || 0).toLocaleString("ko-KR", { maximumFractionDigits: 0 }) + " KRW";
const pct = (value) => Number(value || 0).toFixed(2) + "%";
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
    overview: "운용 현황",
    records: "월/주/일 기록",
    logs: "매매/판단 로그",
    scenarios: "시나리오 결론",
    research: "연구 보관함",
  }[view] || "운용 현황";
}

function content(view, data, account, records) {
  if (view === "overview") return overviewView(records, account);
  if (view === "records") return recordsView(records);
  if (view === "logs") return logsView(data);
  if (view === "scenarios") return scenariosView(records);
  if (view === "research") return researchView(data);
  return overviewView(records, account);
}

function overviewView(records, account) {
  const operating = records.operating_summary || {};
  const conclusion = records.plain_conclusion || {};
  const today = operating.today || latestRow(records.daily || []);
  const week = operating.this_week || latestRow(records.weekly || []);
  const month = operating.this_month || latestRow(records.monthly || []);
  return [
    notice("현재 결론", conclusion.current_operation_conclusion || "V6.8.9 결론 산출물이 아직 없습니다."),
    section("오늘 / 이번주 / 이번달", "매일 확인할 핵심 숫자만 모았습니다.", table([
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
    section("최근 월간 흐름", "최근 월이 위에 옵니다. 자세한 주/일 기록은 월/주/일 기록 탭에서 봅니다.", table(records.monthly || [], ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], 6)),
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
    section(`${month || "선택 월"} 주 기록`, "선택한 월에 속한 주간 기록입니다.", table(weeks, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "candidate_count", "wait_count", "result", "trade_comment"], 80)),
    section(`${month || "선택 월"} 일 기록`, "거래가 없는 날은 거래없음과 이유를 표시합니다.", table(days, ["period", "route_label", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result", "trade_comment"], 200)),
  ].join("");
}

function logsView(data) {
  return [
    section("Forward 후보 로그", "오늘 또는 최근 forward paper 후보와 대기 사유입니다.", table(data.forward_candidate_logs || [], ["time", "market", "strategy_id", "entry_decision", "result", "primary_block_reason", "trade_comment"], 200)),
    section("매수/매도 기록", "실제 paper 체결 로그입니다.", table(data.trade_logs || [], ["time", "market", "action", "route_label", "size_krw", "realized_pnl_krw", "pnl_pct", "reason"], 300)),
    section("시나리오 판단 기록", "각 시점에 적용된 판단 근거입니다.", table(data.scenario_logs || [], ["time", "market", "route_label", "market_state", "action", "guard_on", "dominance_risk", "reason"], 300)),
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
    section("2026 운용 후보 순위", "표본이 부족한 연구용 시나리오는 아래로 내립니다.", table(decision.current_rows || [], ["scenario", "source", "eligible_for_operation", "exclusion_reason", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count", "score", "decision"], 30)),
    section("2022~현재 장기 검증 순위", "장기 복리 성과와 손실 방어를 함께 봅니다.", table(decision.long_term_rows || [], ["scenario", "source", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "trade_count", "score", "decision"], 30)),
  ].join("");
}

function researchView(data) {
  return [
    notice("연구 보관함", "운용 판단에 바로 필요한 자료가 아니므로 별도 탭에 보관했습니다."),
    section("V6.8.8 능동분석", "자동 적용 없이 수동 검토용 경고만 남깁니다.", table(data.active_analysis?.recommendations || [], ["recommendation_id", "trigger_type", "severity", "confidence", "expected_benefit", "allowed_action", "manual_approval_required"], 80)),
    section("판단차이", "사후 결과가 부족하면 UNKNOWN으로 유지합니다.", table(data.disagreement?.rows || [], ["timestamp", "market", "active_decision", "best_decision_ex_post", "disagreement_type", "lesson"], 80)),
    section("수익 반납", "수익 후 1/3/5일 반납률입니다.", table(data.profit_giveback?.rows || [], ["scenario_id", "profit_date", "profit_day_pnl", "giveback_ratio_1d", "giveback_ratio_3d", "giveback_ratio_5d", "recommendation"], 80)),
    section("LLM 복기", "원시 로그 전체가 아니라 요약 input pack 기반입니다.", table([data.llm_daily || {}, data.llm_weekly || {}, data.llm_monthly || {}], ["review_type", "period", "llm_used", "fallback_used", "summary", "active_change_applied", "live_order_allowed"], 5)),
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
  if (key.includes("pct") || key.includes("return") || key.includes("mdd")) return escapeHtml(pct(value));
  if (key === "score") return Number(value || 0).toFixed(2);
  if (typeof value === "boolean") return value ? "예" : "아니오";
  return escapeHtml(String(value));
}

function tone(key, value) {
  if (["pnl_krw", "realized_pnl_krw", "return_pct", "pnl_pct"].includes(key)) {
    const number = Number(value || 0);
    return number > 0 ? "ok" : number < 0 ? "danger" : "";
  }
  if (key === "mdd_pct") return Number(value || 0) < -10 ? "danger" : "";
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
