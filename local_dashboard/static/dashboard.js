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
  route_status: "상태",
  market: "종목",
  action: "행동",
  time: "일시",
  result: "결과",
  trade_count: "거래수",
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
  scenario: "시나리오",
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
  win_rate_pct: "승률",
  avg_win_loss_ratio: "손익비",
  expectancy_krw: "기대손익",
  pattern: "패턴",
  surge_rate_pct: "급등비율",
  surge_count: "급등수",
  recommended_route: "추천 route",
  return_delta_pct: "수익률 차이",
  mdd_delta_pct: "MDD 차이",
};

const money = (value) => Number(value || 0).toLocaleString("ko-KR") + " KRW";
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
  state.data = { health: health.data || {}, account: account.data || {}, records: records.data || {}, payload: payload.data || {} };
  render();
}

function render() {
  const { health, account, records, payload } = state.data;
  const safe = !health.live_order_allowed && !health.real_order_enabled && !health.auto_apply_allowed;
  const stale = records.record_staleness || {};
  const latest = records.latest_record_date || "-";
  const forward = records.latest_forward_ws || {};
  document.querySelector("#status").textContent = safe ? "PAPER 전용 / 실거래 차단" : "실거래 설정 점검 필요";
  document.querySelector("#status").className = safe ? "status" : "status danger";
  document.querySelector("#cards").innerHTML = [
    card("활성 시나리오", account.active_route || records.active_route || payload.active_route || "N/A"),
    card("최신 기록일", latest, stale.status === "STALE" ? "danger" : "ok"),
    card("Forward WS", `${forward.status || "NO_DATA"} / 후보 ${forward.candidate_count ?? 0}`),
    card("주문 안전", safe ? "실거래 차단" : "확인 필요", safe ? "ok" : "danger"),
  ].join("");
  document.querySelector("#view-title").textContent = title(state.view);
  document.querySelector("#content").innerHTML = content(state.view, payload);
  bindRenderedEvents();
}

function card(label, value, tone = "") {
  return `<div class="metric"><div class="label">${label}</div><div class="value ${tone}">${escapeHtml(value ?? "N/A")}</div></div>`;
}

function title(view) {
  return {
    overview: "투자현황",
    records: "월/주/일 투자기록",
    trades: "일자별 매수/매도 로그",
    decisions: "적용 시나리오 판단 로그",
    routes: "시나리오별 월간 비교",
    validation: "급등/손익비/2월 검증",
    risk: "하락장 방어 / ATR 연구",
    control: "관제 요약",
  }[view] || "투자현황";
}

function content(view, data) {
  if (view === "overview") return recordsView(data, true);
  if (view === "records") return recordsView(data, false);
  if (view === "trades") {
    return section("매수/매도 기록", "진입과 청산을 시간순 로그로 분리했습니다.", table(data.trade_logs || [], ["time", "market", "action", "route_id", "route_status", "size_krw", "realized_pnl_krw", "pnl_pct", "reason", "source_mode"], 800));
  }
  if (view === "decisions") {
    return section("시나리오 적용 히스토리", "각 일자·종목별로 어떤 가드와 에이전트 판단이 적용됐는지 확인합니다.", table(data.scenario_logs || [], ["time", "market", "route_id", "market_state", "selected_agent", "action", "size_krw", "guard_on", "hard_guard", "dominance_risk", "pf20", "month_return_pct", "hwm_drawdown_pct", "reason"], 800));
  }
  if (view === "routes") {
    return [
      section("Paper Route-Agent 추천", "자동 실거래 적용은 금지입니다. paper에서 다음 후보만 표시합니다.", table([data.route_agent_recommendation || {}], ["recommended_route", "reason", "return_delta_pct", "mdd_delta_pct", "auto_apply_allowed"], 5)),
      section("시나리오 요약", "최종 수익률, 낙폭, PF를 함께 봅니다.", table(data.routes || [], ["scenario", "route_status", "final_equity_krw", "return_pct", "mdd_pct", "profit_factor", "win_rate_pct", "trade_count", "decision"], 50)),
      section("월별 변화량 비교", "초록색은 해당 월 최고, 붉은색은 해당 월 최저 시나리오입니다.", table(data.monthly_by_route || [], ["period", "route_id", "comparison_rank", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], 500)),
    ].join("");
  }
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
  return recordsView(data, true);
}

function validationView(data) {
  const feb = data.february_feedback || {};
  return [
    section("검증 요약", "", table([
      {
        기간: `${data.data_range?.start || "-"} ~ ${data.data_range?.end || "-"}`,
        거래수: data.data_range?.trade_count || 0,
        판정: data.decision || "-",
        급등정의: data.surge_definition || "-",
      },
    ], ["기간", "거래수", "급등정의", "판정"], 5)),
    section("급등 조건 후보", "pnl_pct 0.50% 이상 거래가 많이 나온 조건입니다.", table(data.surge_patterns || [], ["pattern", "trade_count", "surge_count", "surge_rate_pct", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "expectancy_krw", "interpretation"], 30)),
    section("손익비 패턴", "손익비 = 평균 이익 / 평균 손실, PF = 총이익 / 총손실입니다.", table(data.risk_reward_patterns || [], ["pattern", "trade_count", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "expectancy_krw", "max_drawdown_pct"], 30)),
    section("2월 실패 피드백", "", table(feb.route_monthly_rank || [], ["route_id", "period", "return_pct", "mdd_pct", "trade_count"], 20)),
    section("2월 손실 원인", "", table((feb.insights || []).map((item) => ({ insight: item })), ["insight"], 20)),
    section("낙폭 차단 sweep", "고점대비 낙폭 기준 도달 후 skip 또는 35% 축소했을 때의 사후검증입니다.", table(data.drawdown_cut_sweep || [], ["threshold_hwm_drawdown_pct", "action_when_breached", "total_pnl_krw", "profit_factor", "avg_win_loss_ratio", "win_rate_pct", "max_drawdown_pct"], 20)),
  ].join("");
}

function recordsView(data, compact) {
  const months = data.monthly || [];
  if (!state.selectedMonth && months.length) state.selectedMonth = months[months.length - 1].period;
  const month = state.selectedMonth;
  const weeks = (data.weekly || []).filter((row) => row.month === month);
  const days = (data.daily || []).filter((row) => row.month === month);
  return [
    `<div class="toolbar"><div><b>기준:</b> ${escapeHtml(data.start_date || "2026-01-01")} 이후 · <b>활성:</b> ${escapeHtml(data.active_route || "N/A")} · <b>추천:</b> ${escapeHtml(data.route_agent_recommendation?.recommended_route || "-")} · <b>시장데이터:</b> ${escapeHtml(data.latest_market_data?.latest_time || "-")} · <b>Forward:</b> ${escapeHtml(data.latest_forward_ws?.status || "-")}</div><div class="hint">월 행 클릭 = 해당 월의 주/일 기록 표시</div></div>`,
    section("월단위 투자기록", "큰 흐름과 손실 방어 실패 구간을 먼저 봅니다.", table(months, ["period", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], compact ? 24 : 200, "month-table")),
    section(`${month || "선택 월"} 주단위 기록`, "선택한 월 안에서 어느 주가 수익 또는 손실을 만들었는지 확인합니다.", table(weeks, ["period", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], compact ? 12 : 200)),
    section(`${month || "선택 월"} 일단위 기록`, "일별 손익, 거래수, 낙폭을 로그처럼 추적합니다.", table(days, ["period", "start_equity_krw", "end_equity_krw", "pnl_krw", "return_pct", "mdd_pct", "trade_count", "result"], compact ? 40 : 400)),
  ].join("");
}

function section(titleText, note, body) {
  return `<section class="data-section"><div class="section-head"><h3>${escapeHtml(titleText)}</h3>${note ? `<p>${escapeHtml(note)}</p>` : ""}</div>${body}</section>`;
}

function table(rows, keys, limit = 100, className = "") {
  if (!rows.length) return `<p class="empty">표시할 데이터 없음</p>`;
  const body = rows.slice(0, limit).map((row) => {
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
  if (["pnl_krw", "realized_pnl_krw", "return_pct", "pnl_pct"].includes(key)) {
    const number = Number(value || 0);
    return number > 0 ? "ok" : number < 0 ? "danger" : "";
  }
  if (key === "mdd_pct" || key === "hwm_drawdown_pct") return Number(value || 0) < -10 ? "danger" : "";
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
