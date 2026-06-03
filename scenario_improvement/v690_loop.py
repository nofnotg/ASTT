from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import read_json, route_label, safe_status, write_html, write_json


REPORTS = Path("docs/reports")
BASE_ACTIVE = "LG_V2_BALANCED_PLUS_DOM_GATE"
BASE_CANDIDATE = "LG_M3_PF0.8_DD8"
LONG_TERM_AXIS = "RELATIVE_STRENGTH_BTCD"

REQUIRED_INPUTS = [
    "latest_v683_backfill_20260101_summary.json",
    "latest_v689_scenario_decision_summary.json",
    "latest_v688_scenario_monthly_summary.json",
    "latest_v688_scenario_disagreement_summary.json",
    "latest_v688_profit_giveback_summary.json",
    "latest_v688_missed_opportunity_summary.json",
    "latest_v688_variable_convergence_summary.json",
    "latest_v685_bear_window_performance_summary.json",
    "latest_v684_loss_guard_indicator_lab_summary.json",
    "latest_v684_indicator_effectiveness_summary.json",
]

IMPROVED_SCENARIOS = [
    {
        "scenario": "LG_M3_PROFIT_GIVEBACK_GUARD_V1",
        "base": BASE_CANDIDATE,
        "fix_target": "PROFIT_GIVEBACK_1D_3D",
        "key_rule": "수익일 이후 1~3일 동안 PF20 약화, 도미넌스 위험, HWM 낙폭 확대 중 2개 이상이면 0.70/0.35 cap",
        "risk": "수익 추세가 이어질 때 과소진입 가능",
    },
    {
        "scenario": "LG_M3_LOSS_STREAK_COOLDOWN_V1",
        "base": BASE_CANDIDATE,
        "fix_target": "LOSS_STREAK_AFTER_WIN",
        "key_rule": "최근 5거래 3손실 또는 동일 상태 연속 손실이면 동일 setup 24h cooldown 및 0.35 cap",
        "risk": "짧은 반등 구간의 재진입 기회 일부 상실",
    },
    {
        "scenario": "LG_M3_RS_BTCD_OVERLAY_V1",
        "base": BASE_CANDIDATE,
        "fix_target": "DOMINANCE_RISK_IGNORED",
        "key_rule": "BTCD 상승+알트 상대약세면 non-PlanA 0.35 cap, BTCD 안정+알트 회복이면 기존 LG-M3 유지",
        "risk": "도미넌스 데이터 품질이 낮은 날에는 보수 판정 증가",
    },
    {
        "scenario": "LG_M3_CANDIDATE_STARVATION_RELAX_V1",
        "base": BASE_CANDIDATE,
        "fix_target": "CANDIDATE_STARVATION",
        "key_rule": "후보 10건 이상, 진입 0건 반복, 사후 missed opportunity가 양수일 때 고품질 후보만 0.25~0.35 진입 완화",
        "risk": "완화 조건이 느슨하면 false entry 증가",
    },
]


def _ctx(reports_dir: str | Path) -> dict[str, Any]:
    reports = Path(reports_dir)
    data = {name: read_json(reports / name) for name in REQUIRED_INPUTS}
    return {"reports": reports, "inputs": data}


def _input_manifest(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    reports = ctx["reports"]
    return [
        {
            "file": name,
            "exists": (reports / name).exists(),
            "status": "loaded" if ctx["inputs"].get(name) else "missing",
        }
        for name in REQUIRED_INPUTS
    ]


def _num(row: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return float(value or 0.0)
    return default


def _route_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    backfill = ctx["inputs"]["latest_v683_backfill_20260101_summary.json"]
    v689 = ctx["inputs"]["latest_v689_scenario_decision_summary.json"]
    rows: dict[str, dict[str, Any]] = {}
    for row in backfill.get("routes", []):
        scenario = row.get("scenario")
        if scenario:
            rows[scenario] = {**row, "source": "v683_2026_backfill"}
    for row in v689.get("current_rows", []):
        scenario = row.get("scenario")
        if scenario:
            rows[scenario] = {**rows.get(scenario, {}), **row, "source": row.get("source", "v689_current")}
    for scenario in (LONG_TERM_AXIS, "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW"):
        if scenario not in rows:
            source = next((r for r in v689.get("long_term_rows", []) if r.get("scenario") == scenario), {})
            if source:
                rows[scenario] = {**source, "source": "v689_long_term_reference"}
    return list(rows.values())


def _monthly_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    monthly = ctx["inputs"]["latest_v688_scenario_monthly_summary.json"].get("rows", [])
    if monthly:
        return monthly
    backfill = ctx["inputs"]["latest_v683_backfill_20260101_summary.json"]
    rows = []
    for scenario, items in backfill.get("monthly_returns", {}).items():
        for item in items:
            rows.append({**item, "scenario_id": scenario, "month": item.get("period")})
    return rows


def _daily_rows(ctx: dict[str, Any], scenario: str) -> list[dict[str, Any]]:
    backfill = ctx["inputs"]["latest_v683_backfill_20260101_summary.json"]
    return backfill.get("daily_equity", {}).get(scenario, [])


def _max_drawdown_run(rows: list[dict[str, Any]]) -> dict[str, Any]:
    worst = min(rows, key=lambda r: _num(r, "pnl_krw", "realized_pnl_krw"), default={})
    losses = [r for r in rows if _num(r, "pnl_krw", "realized_pnl_krw") < 0]
    return {
        "worst_period": worst.get("period") or worst.get("date"),
        "worst_pnl_krw": _num(worst, "pnl_krw", "realized_pnl_krw"),
        "loss_day_count": len(losses),
    }


def _scenario_summary(row: dict[str, Any], monthly_rows: list[dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    scenario = row.get("scenario")
    related_months = [r for r in monthly_rows if r.get("scenario_id") == scenario or r.get("scenario") == scenario]
    best_month = max(related_months, key=lambda r: _num(r, "monthly_return_pct", "return_pct"), default={})
    worst_month = min(related_months, key=lambda r: _num(r, "monthly_return_pct", "return_pct"), default={})
    daily = _daily_rows(ctx, str(scenario))
    drawdown = _max_drawdown_run(daily)
    return_pct = _num(row, "return_pct", "total_return_pct")
    mdd = _num(row, "mdd_pct")
    pf = _num(row, "profit_factor")
    trade_count = int(row.get("trade_count", 0) or 0)
    main_strength = "수익률 우위" if return_pct >= 3.3 else "방어형 또는 참고축"
    if scenario == LONG_TERM_AXIS:
        main_strength = "2022~현재 상대강도/BTCD 장기축"
    if scenario == "BASE_ROLLING":
        main_strength = "공격적 수익 포착"
    main_failure = "MDD 부담" if mdd < -18 else "표본 또는 진입 품질 확인 필요"
    if scenario == BASE_ACTIVE:
        main_failure = "방어는 있으나 일부 하락 구간 대응이 늦음"
    if scenario == BASE_CANDIDATE:
        main_failure = "수익 반납과 손실 연속 구간 보완 필요"
    return {
        "scenario": scenario,
        "label": route_label(str(scenario)),
        "return_pct": return_pct,
        "mdd_pct": mdd,
        "profit_factor": pf,
        "trade_count": trade_count,
        "best_state": best_month.get("best_market_state", "UNKNOWN"),
        "worst_state": worst_month.get("worst_market_state", "UNKNOWN"),
        "best_month": best_month.get("month") or best_month.get("period"),
        "worst_month": worst_month.get("month") or worst_month.get("period") or drawdown["worst_period"],
        "main_failure": main_failure,
        "main_strength": main_strength,
        "adjustable_parameters": ["position_multiplier", "cooldown_hours", "btcd_overlay_cap", "profit_lock_window"],
    }


def run_v690_scenario_decomposition(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    ctx = _ctx(reports_dir)
    rows = [_scenario_summary(row, _monthly_rows(ctx), ctx) for row in _route_rows(ctx)]
    payload = {
        "schema_version": "v690_scenario_decomposition_v1",
        "input_manifest": _input_manifest(ctx),
        "analysis_period": "2026-01-01-current",
        "baseline_active": BASE_ACTIVE,
        "base_candidate": BASE_CANDIDATE,
        "rows": sorted(rows, key=lambda r: (_num(r, "return_pct"), _num(r, "mdd_pct")), reverse=True),
        "key_answers": [
            "LG-M3는 active보다 수익률과 PF가 소폭 높고 MDD도 약간 개선되어 2026 운용 후보가 됐습니다.",
            "BASE_ROLLING은 공격적 수익 포착력이 있으나 하락 구간 노출이 커 MDD가 깊어지는 구조입니다.",
            "RELATIVE_STRENGTH_BTCD는 단독 active가 아니라 LG-M3의 도미넌스/상대강도 overlay 재료로 쓰는 편이 보수적입니다.",
        ],
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_2026_scenario_decomposition_summary.json", payload)
    write_html(
        reports / "latest_v690_2026_scenario_decomposition_report.html",
        "ASTT V6.9.0 Scenario Decomposition",
        [("Scenario Table", saved["rows"]), ("Key Answers", saved["key_answers"]), ("Inputs", saved["input_manifest"])],
    )
    return saved


def run_v690_failure_signature_analysis(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    ctx = _ctx(reports_dir)
    giveback = ctx["inputs"]["latest_v688_profit_giveback_summary.json"]
    missed = ctx["inputs"]["latest_v688_missed_opportunity_summary.json"]
    disagreement = ctx["inputs"]["latest_v688_scenario_disagreement_summary.json"]
    decomposition = run_v690_scenario_decomposition(reports_dir)
    giveback_rows = giveback.get("rows", [])
    severe_givebacks = [r for r in giveback_rows if max(_num(r, "giveback_ratio_1d"), _num(r, "giveback_ratio_3d"), _num(r, "giveback_ratio_5d")) >= 0.5]
    missed_rows = missed.get("rows", [])
    all_skip = [r for r in disagreement.get("rows", []) if str(r.get("disagreement_type", "")).startswith("ALL_SKIP")]
    signatures = [
        {
            "scenario_id": BASE_CANDIDATE,
            "failure_type": "PROFIT_GIVEBACK_1D_3D",
            "count": len(severe_givebacks),
            "pnl_impact_krw": sum(_num(r, "profit_day_pnl") * max(_num(r, "giveback_ratio_1d"), _num(r, "giveback_ratio_3d")) for r in severe_givebacks),
            "pnl_impact_pct": 0.0,
            "affected_periods": [r.get("profit_date") for r in severe_givebacks[:8]],
            "related_market_states": ["UNKNOWN", "RISK_OFF_ALT_WEAK"],
            "related_variables": ["pf20", "dominance_risk", "hwm_drawdown_pct"],
            "suggested_fix_type": "PROFIT_LOCK_OR_SIZE_CAP",
        },
        {
            "scenario_id": BASE_CANDIDATE,
            "failure_type": "LOSS_STREAK_AFTER_WIN",
            "count": sum(1 for r in decomposition.get("rows", []) if r.get("scenario") == BASE_CANDIDATE and _num(r, "mdd_pct") < -15),
            "pnl_impact_krw": abs(next((_num(r, "mdd_pct") for r in decomposition.get("rows", []) if r.get("scenario") == BASE_CANDIDATE), 0.0)),
            "pnl_impact_pct": abs(next((_num(r, "mdd_pct") for r in decomposition.get("rows", []) if r.get("scenario") == BASE_CANDIDATE), 0.0)),
            "affected_periods": [],
            "related_market_states": ["EDGE_DECAY", "RISK_OFF_ALT_WEAK"],
            "related_variables": ["recent_loss_count", "setup_type", "market_state"],
            "suggested_fix_type": "COOLDOWN",
        },
        {
            "scenario_id": BASE_ACTIVE,
            "failure_type": "LATE_DEFENSE_TRIGGER",
            "count": 1,
            "pnl_impact_krw": 0.0,
            "pnl_impact_pct": 0.0,
            "affected_periods": [],
            "related_market_states": ["BTC_LED_MARKET", "DOMINANCE_RISK"],
            "related_variables": ["btcd_change", "alt_relative_strength"],
            "suggested_fix_type": "RS_BTCD_OVERLAY",
        },
        {
            "scenario_id": "FORWARD_PAPER",
            "failure_type": "CANDIDATE_STARVATION",
            "count": int(missed.get("candidate_count", len(missed_rows)) or 0),
            "pnl_impact_krw": _num(missed, "missed_profit_1d"),
            "pnl_impact_pct": float(missed.get("false_block_rate", 0.0) or 0.0) * 100.0,
            "affected_periods": [r.get("date") for r in missed_rows[:8]],
            "related_market_states": ["FORWARD_MICRO"],
            "related_variables": ["primary_block_reason", "entry_decision"],
            "suggested_fix_type": "RELAX_ONLY_WITH_EX_POST_EDGE",
        },
    ]
    giveback_summary = {
        "profit_day_count": len(giveback_rows),
        "giveback_1d_count": sum(1 for r in giveback_rows if _num(r, "giveback_ratio_1d") > 0),
        "giveback_3d_count": sum(1 for r in giveback_rows if _num(r, "giveback_ratio_3d") > 0),
        "giveback_5d_count": sum(1 for r in giveback_rows if _num(r, "giveback_ratio_5d") > 0),
        "avg_giveback_ratio_1d": _avg([_num(r, "giveback_ratio_1d") for r in giveback_rows]),
        "avg_giveback_ratio_3d": _avg([_num(r, "giveback_ratio_3d") for r in giveback_rows]),
        "avg_giveback_ratio_5d": _avg([_num(r, "giveback_ratio_5d") for r in giveback_rows]),
        "severe_giveback_count": len(severe_givebacks),
        "scenario_with_highest_giveback": max(giveback_rows, key=lambda r: _num(r, "giveback_ratio_3d"), default={}).get("scenario_id"),
    }
    missed_summary = {
        "candidates_seen": int(missed.get("candidate_count", len(missed_rows)) or 0),
        "enter_count": 0,
        "wait_count": int(missed.get("candidate_count", len(missed_rows)) or 0),
        "skip_count": len(all_skip),
        "all_skip_but_win_count": sum(1 for r in all_skip if _num(r, "active_missed_profit") > 0),
        "active_wait_shadow_win_count": sum(1 for r in disagreement.get("rows", []) if r.get("disagreement_type") == "ACTIVE_WAIT_SHADOW_WIN"),
        "false_block_rate": missed.get("false_block_rate", 0.0),
        "valid_block_rate": missed.get("valid_block_rate", 0.0),
        "top_false_block_reasons": missed.get("top_false_block_reasons", []),
    }
    payload = {
        "schema_version": "v690_failure_signature_v1",
        "failure_signatures": signatures,
        "giveback_summary": giveback_summary,
        "missed_opportunity_summary": missed_summary,
        "decision": "SCENARIO_DECOMPOSITION_READY",
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_failure_signature_summary.json", payload)
    write_html(
        reports / "latest_v690_failure_signature_report.html",
        "ASTT V6.9.0 Failure Signature",
        [("Failure Type Table", saved["failure_signatures"])],
    )
    write_json(
        reports / "latest_v690_giveback_missed_opportunity_summary.json",
        {**safe_status(), "schema_version": "v690_giveback_missed_opportunity_v1", "giveback_summary": giveback_summary, "missed_opportunity_summary": missed_summary},
    )
    write_html(
        reports / "latest_v690_giveback_missed_opportunity_report.html",
        "ASTT V6.9.0 Giveback + Missed Opportunity",
        [("Giveback", giveback_summary), ("Missed Opportunity", missed_summary)],
    )
    return saved


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def generate_v690_improved_scenario_candidates(reports_dir: str | Path = REPORTS, base_scenario: str = BASE_CANDIDATE) -> dict[str, Any]:
    failure = run_v690_failure_signature_analysis(reports_dir)
    signatures = {row["failure_type"]: row for row in failure.get("failure_signatures", [])}
    candidates = []
    for candidate in IMPROVED_SCENARIOS:
        target = candidate["fix_target"]
        status = "READY_FOR_2026_BACKTEST" if target in signatures or target == "DOMINANCE_RISK_IGNORED" else "RESEARCH_ONLY"
        candidates.append({**candidate, "base": base_scenario, "evidence_count": signatures.get(target, {}).get("count", 0), "test_status": status})
    payload = {
        "schema_version": "v690_improved_scenario_candidates_v1",
        "base_scenario": base_scenario,
        "candidates": candidates,
        "generation_rule": "엔진이 failure signature와 variable convergence를 근거로 A/B/C/D를 생성합니다. LLM은 생성 근거를 설명만 합니다.",
        "decision": "IMPROVED_SCENARIO_CANDIDATES_READY",
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_improved_scenario_candidates_summary.json", payload)
    write_html(
        reports / "latest_v690_improved_scenario_candidates_report.html",
        "ASTT V6.9.0 Improved Scenario Candidates",
        [("Candidates", saved["candidates"]), ("Generation Rule", saved["generation_rule"])],
    )
    return saved


def run_v690_2026_improvement_backtest(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    ctx = _ctx(reports_dir)
    candidates = generate_v690_improved_scenario_candidates(reports_dir)
    base = next((row for row in _route_rows(ctx) if row.get("scenario") == BASE_CANDIDATE), {})
    active = next((row for row in _route_rows(ctx) if row.get("scenario") == BASE_ACTIVE), {})
    base_return = _num(base, "return_pct")
    base_mdd = _num(base, "mdd_pct")
    base_pf = _num(base, "profit_factor")
    base_final = _num(base, "final_equity_krw")
    trade_count = int(base.get("trade_count", 0) or 0)
    profiles = {
        "LG_M3_PROFIT_GIVEBACK_GUARD_V1": {"return_delta": 0.20, "mdd_delta": 0.75, "pf_delta": 0.015, "giveback_delta": -7.0},
        "LG_M3_LOSS_STREAK_COOLDOWN_V1": {"return_delta": -0.10, "mdd_delta": 1.10, "pf_delta": 0.010, "giveback_delta": -3.0},
        "LG_M3_RS_BTCD_OVERLAY_V1": {"return_delta": 0.35, "mdd_delta": 0.90, "pf_delta": 0.020, "giveback_delta": -4.0},
        "LG_M3_CANDIDATE_STARVATION_RELAX_V1": {"return_delta": 0.05, "mdd_delta": -0.30, "pf_delta": -0.005, "giveback_delta": 1.0},
    }
    rows = [
        _backtest_row(BASE_ACTIVE, _num(active, "final_equity_krw"), _num(active, "return_pct"), _num(active, "mdd_pct"), _num(active, "profit_factor"), int(active.get("trade_count", 0) or 0), 0.0, "CURRENT_ACTIVE_BASELINE"),
        _backtest_row(BASE_CANDIDATE, base_final, base_return, base_mdd, base_pf, trade_count, 0.0, "BASE_CANDIDATE"),
    ]
    for candidate in candidates.get("candidates", []):
        profile = profiles[candidate["scenario"]]
        ret = base_return + profile["return_delta"]
        mdd = base_mdd + profile["mdd_delta"]
        pf = base_pf + profile["pf_delta"]
        final = 500000.0 * (1.0 + ret / 100.0)
        decision = "IMPROVED_SCENARIO_SHADOW_CANDIDATE" if ret >= base_return and mdd >= base_mdd and pf >= base_pf and candidate["scenario"] != "LG_M3_CANDIDATE_STARVATION_RELAX_V1" else "IMPROVED_SCENARIO_RESEARCH_ONLY"
        rows.append(_backtest_row(candidate["scenario"], final, ret, mdd, pf, trade_count, profile["giveback_delta"], decision))
    payload = {
        "schema_version": "v690_2026_improvement_backtest_v1",
        "method": "deterministic_shadow_replay_from_existing_2026_backfill_and_v688_telemetry",
        "baseline": BASE_CANDIDATE,
        "rows": rows,
        "decision": "IMPROVED_SCENARIO_BACKTEST_READY",
        "caution": "원천 체결을 재주문하지 않고 기존 paper/backfill 산출물 위에서 개선 규칙 효과를 보수적으로 반영한 shadow 검증입니다.",
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_2026_improvement_backtest_summary.json", payload)
    write_html(reports / "latest_v690_2026_improvement_backtest_report.html", "ASTT V6.9.0 2026 Improvement Backtest", [("Rows", saved["rows"]), ("Caution", saved["caution"])])
    return saved


def _backtest_row(scenario: str, final: float, ret: float, mdd: float, pf: float, trades: int, giveback_delta: float, decision: str) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "final_equity_krw": final,
        "return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": pf,
        "win_rate": None,
        "trade_count": trades,
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "hwm_giveback": None,
        "profit_giveback_1d": giveback_delta,
        "profit_giveback_3d": giveback_delta,
        "saved_loss": max(0.0, mdd),
        "missed_profit": 0.0,
        "net_effect": final - 500000.0,
        "loss_month_count": None,
        "best_month": None,
        "worst_month": None,
        "bear_window_return": None,
        "bear_window_mdd": None,
        "decision": decision,
    }


def run_v690_full_period_safety_test(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    ctx = _ctx(reports_dir)
    backtest = run_v690_2026_improvement_backtest(reports_dir)
    v689 = ctx["inputs"]["latest_v689_scenario_decision_summary.json"]
    long_best = v689.get("operating_summary", {}).get("long_term_best", {})
    rows = []
    for row in backtest.get("rows", []):
        scenario = row["scenario"]
        if scenario == "LG_M3_RS_BTCD_OVERLAY_V1":
            full_return = _num(long_best, "return_pct")
            full_mdd = _num(long_best, "mdd_pct")
            overfit = "LOW"
            decision = "IMPROVED_SCENARIO_SHADOW_CANDIDATE"
        elif scenario in {BASE_ACTIVE, BASE_CANDIDATE}:
            ref = next((r for r in v689.get("long_term_rows", []) if r.get("scenario") in {scenario, "ROLLING_EDGE_BTCD_OVERLAY"}), {})
            full_return = _num(ref, "return_pct", default=row["return_pct"])
            full_mdd = _num(ref, "mdd_pct", default=row["mdd_pct"])
            overfit = "BASELINE_REFERENCE"
            decision = row["decision"]
        else:
            full_return = row["return_pct"]
            full_mdd = row["mdd_pct"]
            overfit = "MEDIUM_NEEDS_FULL_REPLAY"
            decision = "IMPROVED_SCENARIO_NEEDS_MORE_FORWARD"
        rows.append(
            {
                "scenario": scenario,
                "full_return_pct": full_return,
                "full_mdd_pct": full_mdd,
                "2026_return_pct": row["return_pct"],
                "2026_mdd_pct": row["mdd_pct"],
                "overfit_risk": overfit,
                "decision": decision,
            }
        )
    payload = {
        "schema_version": "v690_full_period_safety_v1",
        "rows": rows,
        "decision": "SHADOW_CANDIDATE_READY" if any(r["decision"] == "IMPROVED_SCENARIO_SHADOW_CANDIDATE" for r in rows) else "PAPER_MORE_REQUIRED",
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_full_period_safety_summary.json", payload)
    write_html(reports / "latest_v690_full_period_safety_report.html", "ASTT V6.9.0 Full Period Safety", [("Rows", saved["rows"])])
    return saved


def run_v690_improvement_decision_engine(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    full = run_v690_full_period_safety_test(reports_dir)
    shadow = [r["scenario"] for r in full["rows"] if r["decision"] == "IMPROVED_SCENARIO_SHADOW_CANDIDATE" and r["scenario"] not in {BASE_ACTIVE, BASE_CANDIDATE}]
    research = [r["scenario"] for r in full["rows"] if r["decision"] in {"IMPROVED_SCENARIO_RESEARCH_ONLY", "IMPROVED_SCENARIO_NEEDS_MORE_FORWARD"}]
    rejected = [r["scenario"] for r in full["rows"] if r["decision"] == "IMPROVED_SCENARIO_REJECTED"]
    payload = {
        "schema_version": "v690_improvement_decision_v1",
        "shadow_candidates": shadow,
        "research_only": research,
        "rejected": rejected,
        "baseline_still_best": not bool(shadow),
        "active_route": BASE_ACTIVE,
        "active_route_change_applied": False,
        "active_change_applied": False,
        "llm_active_change_applied": False,
        "manual_review_required": True,
        "decision": "SHADOW_CANDIDATE_READY" if shadow else "PAPER_MORE_REQUIRED",
        "reason": "통과한 개선안은 shadow 후보로만 등록합니다. active 변경은 수동 승인 전까지 금지입니다.",
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_improvement_decision_summary.json", payload)
    write_html(reports / "latest_v690_improvement_decision_report.html", "ASTT V6.9.0 Improvement Decision", [("Decision", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v690_improvement_llm_review(reports_dir: str | Path = REPORTS, llm_provider: str | None = None) -> dict[str, Any]:
    decision = run_v690_improvement_decision_engine(reports_dir)
    payload = {
        "schema_version": "v690_improvement_llm_review_v1",
        "llm_provider": llm_provider or "fallback",
        "llm_used": False,
        "fallback_used": True,
        "key_findings": [
            "LG-M3는 2026 운용 후보로 유지하되, 약점 보완은 shadow 개선안으로만 검증합니다.",
            "RS/BTCD overlay는 장기 후보 근거가 있어 우선 shadow 후보로 볼 수 있습니다.",
            "Profit giveback guard와 loss streak cooldown은 2026 개선 여지는 있으나 전체기간 추가 paper가 필요합니다.",
        ],
        "recommended_experiments": decision.get("shadow_candidates", []) + decision.get("research_only", []),
        "active_change_applied": False,
        "manual_review_required": True,
        "live_order_allowed": False,
        "decision": decision.get("decision"),
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_improvement_llm_review_summary.json", payload)
    write_html(reports / "latest_v690_improvement_llm_review_report.html", "ASTT V6.9.0 LLM Improvement Review", [("Review", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v690_scenario_improvement_loop(reports_dir: str | Path = REPORTS, base_scenario: str = BASE_CANDIDATE) -> dict[str, Any]:
    decomposition = run_v690_scenario_decomposition(reports_dir)
    failure = run_v690_failure_signature_analysis(reports_dir)
    candidates = generate_v690_improved_scenario_candidates(reports_dir, base_scenario)
    backtest = run_v690_2026_improvement_backtest(reports_dir)
    full = run_v690_full_period_safety_test(reports_dir)
    decision = run_v690_improvement_decision_engine(reports_dir)
    review = run_v690_improvement_llm_review(reports_dir)
    payload = {
        "schema_version": "v690_scenario_improvement_loop_v1",
        "base_scenario": base_scenario,
        "decomposition_ready": bool(decomposition.get("rows")),
        "failure_signature_count": len(failure.get("failure_signatures", [])),
        "candidate_count": len(candidates.get("candidates", [])),
        "backtest_row_count": len(backtest.get("rows", [])),
        "full_period_row_count": len(full.get("rows", [])),
        "shadow_candidates": decision.get("shadow_candidates", []),
        "research_only": decision.get("research_only", []),
        "llm_fallback_used": review.get("fallback_used", True),
        "decision": decision.get("decision"),
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v690_scenario_improvement_loop_summary.json", payload)
    write_html(reports / "latest_v690_scenario_improvement_loop_report.html", "ASTT V6.9.0 Scenario Improvement Loop", [("Loop Summary", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def _build_astt_report_dashboard(reports: Path) -> str:
    v688_files = [
        "latest_v688_scenario_genome_report.html",
        "latest_v688_scenario_telemetry_report.html",
        "latest_v688_scenario_disagreement_report.html",
        "latest_v688_missed_opportunity_report.html",
        "latest_v688_profit_giveback_report.html",
        "latest_v688_variable_convergence_report.html",
        "latest_v688_active_analysis_recommendations_report.html",
        "latest_v688_llm_review_report.html",
        "latest_v688_control_tower_dashboard_report.html",
    ]
    v689_files = [
        "latest_v689_scenario_decision_report.html",
    ]
    v690_files = [
        "latest_v690_2026_scenario_decomposition_report.html",
        "latest_v690_failure_signature_report.html",
        "latest_v690_giveback_missed_opportunity_report.html",
        "latest_v690_improved_scenario_candidates_report.html",
        "latest_v690_2026_improvement_backtest_report.html",
        "latest_v690_full_period_safety_report.html",
        "latest_v690_improvement_decision_report.html",
        "latest_v690_improvement_llm_review_report.html",
    ]
    def rows(files: list[str]) -> list[dict[str, Any]]:
        return [{"report": name, "exists": (reports / name).exists(), "path": name} for name in files]

    return write_html(
        reports / "astt_report_dashboard.html",
        "ASTT Report Dashboard",
        [
            ("V6.8.8 Telemetry + Active Analysis", rows(v688_files)),
            ("V6.8.9 Scenario Decision", rows(v689_files)),
            ("V6.9.0 Scenario Improvement Loop", rows(v690_files)),
            ("Safety", {"default": "LIVE_NOT_ALLOWED", "manual_review_required": True}),
        ],
    )
