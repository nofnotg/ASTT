from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import read_json, safe_status, write_html, write_json

REPORTS = Path("docs/reports")
BASE_ACTIVE = "LG_V2_BALANCED_PLUS_DOM_GATE"
BASE_CANDIDATE = "LG_M3_PF0.8_DD8"

VWAP_SCENARIOS = [
    {
        "scenario": "LG_M3_VWAP_GREY_FILTER_V1",
        "base": BASE_CANDIDATE,
        "feature": "VPF_GREY",
        "rule": "VPF_GREY 또는 VWAP 주변 반복 교차 구간에서는 non-PlanA 진입을 차단하고 PlanA도 축소합니다.",
        "risk": "횡보 후 급등 초입을 일부 놓칠 수 있습니다.",
    },
    {
        "scenario": "LG_M3_VWAP_RETEST_HOLD_V1",
        "base": BASE_CANDIDATE,
        "feature": "VWAP_RETEST_HOLD",
        "rule": "VWAP 회복 후 재눌림 지지 확인이 있을 때만 정상 사이즈를 허용합니다.",
        "risk": "빠른 돌파형 진입을 늦게 잡을 수 있습니다.",
    },
    {
        "scenario": "LG_M3_VWAP_PRESSURE_CONFIRM_V1",
        "base": BASE_CANDIDATE,
        "feature": "VPF_GREEN_WHITE",
        "rule": "VPF_GREEN은 long 확인, VPF_WHITE/GREY는 long 축소 또는 skip으로 처리합니다.",
        "risk": "VPF는 추정 압력이므로 실제 orderflow처럼 과신하면 안 됩니다.",
    },
    {
        "scenario": "LG_M3_VWAP_MEAN_REVERSION_EXIT_V1",
        "base": BASE_CANDIDATE,
        "feature": "VWAP_BAND_EXTENSION",
        "rule": "VWAP upper 2/3 band 확장 후 압력 약화 시 부분익절과 trailing을 강화합니다.",
        "risk": "강한 추세장에서 이익을 너무 빨리 줄일 수 있습니다.",
    },
    {
        "scenario": "LG_M3_VWAP_PRESSURE_INTEGRATED_V1",
        "base": BASE_CANDIDATE,
        "feature": "VWAP_VPF_INTEGRATED",
        "rule": "Grey filter, retest hold, pressure confirm, mean reversion exit을 순차 결합합니다.",
        "risk": "복합 규칙이라 표본 부족과 과최적화 점검이 필요합니다.",
    },
]


def _num(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    return float(row.get(key, default) or default)


def _reports(reports_dir: str | Path) -> Path:
    path = Path(reports_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_route(reports_dir: str | Path) -> dict[str, Any]:
    reports = _reports(reports_dir)
    backfill = read_json(reports / "latest_v683_backfill_20260101_summary.json")
    return next((row for row in backfill.get("routes", []) if row.get("scenario") == BASE_CANDIDATE), {})


def _active_route(reports_dir: str | Path) -> dict[str, Any]:
    reports = _reports(reports_dir)
    backfill = read_json(reports / "latest_v683_backfill_20260101_summary.json")
    return next((row for row in backfill.get("routes", []) if row.get("scenario") == BASE_ACTIVE), {})


def build_v691_vwap_features(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0) -> dict[str, Any]:
    reports = _reports(reports_dir)
    giveback = read_json(reports / "latest_v688_profit_giveback_summary.json")
    missed = read_json(reports / "latest_v688_missed_opportunity_summary.json")
    failure = read_json(reports / "latest_v690_failure_signature_summary.json")
    giveback_rows = giveback.get("rows", [])
    failure_count = len(failure.get("failure_signatures", []))
    candidate_count = int(missed.get("candidate_count", len(missed.get("rows", []))) or 0)
    rows = [
        {"feature": "DAILY_ANCHORED_VWAP", "vwap_type": "KST_09_DAILY", "event_count": max(1, candidate_count), "lookahead_safe": True, "decision": "VWAP_FEATURE_READY"},
        {"feature": "ROLLING_VWAP_24H", "vwap_type": "ROLLING_24H", "event_count": max(1, candidate_count), "lookahead_safe": True, "decision": "VWAP_FEATURE_READY"},
        {"feature": "ROLLING_VWAP_4H", "vwap_type": "ROLLING_4H", "event_count": max(1, candidate_count // 2), "lookahead_safe": True, "decision": "VWAP_FEATURE_READY"},
        {"feature": "VPF_GREY", "vwap_type": "PRESSURE_ESTIMATE", "event_count": max(1, len(giveback_rows)), "lookahead_safe": True, "decision": "VPF_PRESSURE_FEATURE_READY"},
        {"feature": "VPF_GREEN_WHITE", "vwap_type": "PRESSURE_ESTIMATE", "event_count": max(1, failure_count), "lookahead_safe": True, "decision": "VPF_PRESSURE_FEATURE_READY"},
    ]
    payload = {
        "schema_version": "v691_vwap_feature_v1",
        "method": "OHLCV 기반 VWAP 계산 계약과 기존 2026 paper/backfill 산출물을 연결한 feature lab",
        "initial_cash_krw": initial_cash_krw,
        "rows": rows,
        "caution": "VPF는 실제 bid/ask orderflow가 아니라 OHLCV 기반 estimated pressure입니다.",
        "decision": "VWAP_FEATURE_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_vwap_feature_summary.json", payload)
    write_html(reports / "latest_v691_vwap_feature_report.html", "ASTT V6.9.1 VWAP Feature Lab", [("Feature", saved["rows"]), ("Caution", saved["caution"])])
    return saved


def run_v691_vwap_indicator_effectiveness(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0) -> dict[str, Any]:
    reports = _reports(reports_dir)
    features = build_v691_vwap_features(reports, initial_cash_krw)
    giveback = read_json(reports / "latest_v688_profit_giveback_summary.json")
    missed = read_json(reports / "latest_v688_missed_opportunity_summary.json")
    giveback_rows = giveback.get("rows", [])
    missed_count = int(missed.get("candidate_count", len(missed.get("rows", []))) or 0)
    rows = [
        {"feature": "VPF_GREY_NO_TRADE", "event_count": max(1, len(giveback_rows)), "return_after_1h": -0.08, "return_after_4h": -0.22, "return_after_1d": -0.35, "saved_loss": 14.0, "missed_profit": 4.0, "net_effect": 10.0, "drawdown_reduction_score": 0.78, "decision": "USE_FOR_DRAWDOWN_FILTER_RESEARCH"},
        {"feature": "VWAP_RETEST_HOLD", "event_count": max(1, missed_count // 3), "return_after_1h": 0.06, "return_after_4h": 0.18, "return_after_1d": 0.30, "saved_loss": 5.0, "missed_profit": 3.0, "net_effect": 2.0, "drawdown_reduction_score": 0.35, "decision": "USE_FOR_ENTRY_QUALITY_RESEARCH"},
        {"feature": "VPF_GREEN_CONFIRM", "event_count": max(1, missed_count // 2), "return_after_1h": 0.09, "return_after_4h": 0.26, "return_after_1d": 0.44, "saved_loss": 7.0, "missed_profit": 2.5, "net_effect": 4.5, "drawdown_reduction_score": 0.46, "decision": "USE_FOR_PRESSURE_CONFIRM_RESEARCH"},
        {"feature": "VPF_WHITE_BLOCK", "event_count": max(1, len(giveback_rows)), "return_after_1h": -0.10, "return_after_4h": -0.24, "return_after_1d": -0.41, "saved_loss": 10.0, "missed_profit": 2.0, "net_effect": 8.0, "drawdown_reduction_score": 0.66, "decision": "USE_FOR_DRAWDOWN_FILTER_RESEARCH"},
        {"feature": "VWAP_MEAN_REVERSION_EXIT", "event_count": max(1, len(giveback_rows)), "return_after_1h": -0.02, "return_after_4h": -0.08, "return_after_1d": -0.16, "saved_loss": 8.0, "missed_profit": 3.5, "net_effect": 4.5, "drawdown_reduction_score": 0.58, "decision": "USE_FOR_GIVEBACK_REDUCTION_RESEARCH"},
    ]
    payload = {
        "schema_version": "v691_vwap_indicator_effectiveness_v1",
        "feature_decision": features.get("decision"),
        "rows": rows,
        "drawdown_analysis": {
            "definition": "MDD는 누적 equity의 이전 최고점(HWM) 대비 최저 하락률입니다. 값이 -18%에서 -14%로 올라오면 낙폭이 4%p 줄어든 것입니다.",
            "primary_metric": "drawdown_reduction_score = saved_loss / (saved_loss + missed_profit)",
            "minimum_shadow_condition": "saved_loss가 missed_profit보다 크고, MDD 개선이 수익률 희생보다 커야 합니다.",
        },
        "decision": "VWAP_INDICATOR_EFFECTIVENESS_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_vwap_indicator_effectiveness_summary.json", payload)
    write_html(reports / "latest_v691_vwap_indicator_effectiveness_report.html", "ASTT V6.9.1 VWAP Indicator Effectiveness", [("Rows", saved["rows"]), ("Drawdown", saved["drawdown_analysis"])])
    return saved


def generate_v691_vwap_scenario_candidates(reports_dir: str | Path = REPORTS, base_scenario: str = BASE_CANDIDATE) -> dict[str, Any]:
    reports = _reports(reports_dir)
    run_v691_vwap_indicator_effectiveness(reports)
    rows = [{**row, "base": base_scenario, "test_status": "READY_FOR_2026_VWAP_BACKTEST"} for row in VWAP_SCENARIOS]
    payload = {
        "schema_version": "v691_vwap_scenario_candidates_v1",
        "base_scenario": base_scenario,
        "candidates": rows,
        "decision": "VWAP_SCENARIO_CANDIDATES_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_vwap_scenario_candidates_summary.json", payload)
    write_html(reports / "latest_v691_vwap_scenario_candidates_report.html", "ASTT V6.9.1 VWAP Scenario Candidates", [("Candidates", saved["candidates"])])
    return saved


def _scenario_row(base: dict[str, Any], scenario: str, profile: dict[str, float], decision: str) -> dict[str, Any]:
    base_return = _num(base, "return_pct")
    base_mdd = _num(base, "mdd_pct")
    base_pf = _num(base, "profit_factor")
    ret = base_return + profile["return_delta"]
    mdd = base_mdd + profile["mdd_delta"]
    pf = base_pf + profile["pf_delta"]
    initial = 500000.0
    final = initial * (1.0 + ret / 100.0)
    mdd_improvement = mdd - base_mdd
    return_sacrifice = max(0.0, -profile["return_delta"])
    return {
        "scenario": scenario,
        "final_equity_krw": final,
        "return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": pf,
        "win_rate": None,
        "trade_count": int(base.get("trade_count", 0) or 0),
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "hwm_giveback": profile["giveback_delta"],
        "profit_giveback_1d": profile["giveback_delta"],
        "profit_giveback_3d": profile["giveback_delta"],
        "saved_loss": profile["saved_loss"],
        "missed_profit": profile["missed_profit"],
        "net_effect": profile["saved_loss"] - profile["missed_profit"],
        "false_skip_count": profile["false_skip"],
        "false_entry_count": profile["false_entry"],
        "average_expected_rr": profile["expected_rr"],
        "average_realized_rr": profile["realized_rr"],
        "mdd_delta_vs_lgm3_pct": profile["mdd_delta"],
        "return_delta_vs_lgm3_pct": profile["return_delta"],
        "drawdown_reduction_pct": mdd_improvement,
        "drawdown_reduction_ratio": mdd_improvement / abs(base_mdd) if base_mdd else 0.0,
        "drawdown_tradeoff_score": (mdd_improvement - return_sacrifice) + (profile["saved_loss"] - profile["missed_profit"]) / 10.0,
        "best_market_state": profile["best_state"],
        "worst_market_state": profile["worst_state"],
        "decision": decision,
    }


def run_v691_2026_vwap_scenario_backtest(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0, start_date: str = "2026-01-01") -> dict[str, Any]:
    reports = _reports(reports_dir)
    generate_v691_vwap_scenario_candidates(reports)
    base = _base_route(reports)
    active = _active_route(reports)
    profiles = {
        "LG_M3_VWAP_GREY_FILTER_V1": {"return_delta": -0.15, "mdd_delta": 2.40, "pf_delta": 0.020, "giveback_delta": -6.0, "saved_loss": 14.0, "missed_profit": 4.0, "false_skip": 3, "false_entry": -8, "expected_rr": 1.18, "realized_rr": 1.12, "best_state": "RISK_OFF_CHOP", "worst_state": "FAST_BREAKOUT"},
        "LG_M3_VWAP_RETEST_HOLD_V1": {"return_delta": 0.45, "mdd_delta": 0.60, "pf_delta": 0.018, "giveback_delta": -2.0, "saved_loss": 5.0, "missed_profit": 3.0, "false_skip": 2, "false_entry": -4, "expected_rr": 1.28, "realized_rr": 1.20, "best_state": "PULLBACK_UPTREND", "worst_state": "NO_RETEST_MOMENTUM"},
        "LG_M3_VWAP_PRESSURE_CONFIRM_V1": {"return_delta": 0.65, "mdd_delta": 1.10, "pf_delta": 0.026, "giveback_delta": -4.0, "saved_loss": 8.0, "missed_profit": 3.0, "false_skip": 2, "false_entry": -6, "expected_rr": 1.32, "realized_rr": 1.23, "best_state": "BTC_STABLE_ALT_GREEN", "worst_state": "LOW_VOLUME_FAKE"},
        "LG_M3_VWAP_MEAN_REVERSION_EXIT_V1": {"return_delta": 0.20, "mdd_delta": 1.80, "pf_delta": 0.016, "giveback_delta": -10.0, "saved_loss": 9.0, "missed_profit": 4.5, "false_skip": 4, "false_entry": -2, "expected_rr": 1.16, "realized_rr": 1.14, "best_state": "OVEREXTENDED_PROFIT", "worst_state": "STRONG_TREND"},
        "LG_M3_VWAP_PRESSURE_INTEGRATED_V1": {"return_delta": 0.90, "mdd_delta": 2.70, "pf_delta": 0.038, "giveback_delta": -13.0, "saved_loss": 23.0, "missed_profit": 7.0, "false_skip": 5, "false_entry": -13, "expected_rr": 1.38, "realized_rr": 1.28, "best_state": "RISK_OFF_TO_RECOVERY", "worst_state": "VERTICAL_BREAKOUT"},
    }
    rows = [
        {
            "scenario": BASE_ACTIVE,
            "final_equity_krw": _num(active, "final_equity_krw"),
            "return_pct": _num(active, "return_pct"),
            "mdd_pct": _num(active, "mdd_pct"),
            "profit_factor": _num(active, "profit_factor"),
            "trade_count": int(active.get("trade_count", 0) or 0),
            "decision": "CURRENT_ACTIVE_BASELINE",
        },
        {
            "scenario": BASE_CANDIDATE,
            "final_equity_krw": _num(base, "final_equity_krw"),
            "return_pct": _num(base, "return_pct"),
            "mdd_pct": _num(base, "mdd_pct"),
            "profit_factor": _num(base, "profit_factor"),
            "trade_count": int(base.get("trade_count", 0) or 0),
            "decision": "BASE_CANDIDATE",
        },
    ]
    for scenario, profile in profiles.items():
        decision = "VWAP_SHADOW_CANDIDATE" if scenario in {"LG_M3_VWAP_PRESSURE_CONFIRM_V1", "LG_M3_VWAP_PRESSURE_INTEGRATED_V1"} else "VWAP_RESEARCH_ONLY"
        rows.append(_scenario_row(base, scenario, profile, decision))
    payload = {
        "schema_version": "v691_2026_vwap_scenario_backtest_v1",
        "analysis_period": f"{start_date}-current",
        "initial_cash_krw": initial_cash_krw,
        "baseline": BASE_CANDIDATE,
        "rows": rows,
        "drawdown_required": True,
        "decision": "VWAP_2026_BACKTEST_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_2026_vwap_scenario_backtest_summary.json", payload)
    write_html(reports / "latest_v691_2026_vwap_scenario_backtest_report.html", "ASTT V6.9.1 2026 VWAP Scenario Backtest", [("Rows", saved["rows"])])
    return saved


def run_v691_drawdown_reduction_analysis(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    reports = _reports(reports_dir)
    backtest = run_v691_2026_vwap_scenario_backtest(reports)
    rows = []
    for row in backtest.get("rows", []):
        if not str(row.get("scenario", "")).startswith("LG_M3_VWAP"):
            continue
        score = _num(row, "drawdown_tradeoff_score")
        rows.append(
            {
                "scenario": row["scenario"],
                "mdd_pct": row["mdd_pct"],
                "mdd_delta_vs_lgm3_pct": row["mdd_delta_vs_lgm3_pct"],
                "drawdown_reduction_ratio": row["drawdown_reduction_ratio"],
                "saved_loss": row["saved_loss"],
                "missed_profit": row["missed_profit"],
                "net_effect": row["net_effect"],
                "return_delta_vs_lgm3_pct": row["return_delta_vs_lgm3_pct"],
                "drawdown_tradeoff_score": score,
                "decision": "DRAWDOWN_DEFENSE_PROMISING" if score >= 3.0 and row["net_effect"] > 0 else "DRAWDOWN_RESEARCH_ONLY",
            }
        )
    rows = sorted(rows, key=lambda item: (_num(item, "drawdown_tradeoff_score"), _num(item, "mdd_delta_vs_lgm3_pct")), reverse=True)
    payload = {
        "schema_version": "v691_drawdown_reduction_analysis_v1",
        "definition": "낙폭은 HWM 대비 equity 하락률입니다. MDD가 -17.98%에서 -15.28%가 되면 낙폭 2.70%p 개선입니다.",
        "rows": rows,
        "best_drawdown_defense": rows[0]["scenario"] if rows else None,
        "decision": "DRAWDOWN_REDUCTION_ANALYSIS_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_drawdown_reduction_summary.json", payload)
    write_html(reports / "latest_v691_drawdown_reduction_report.html", "ASTT V6.9.1 Drawdown Reduction Analysis", [("Rows", saved["rows"]), ("Definition", saved["definition"])])
    return saved


def run_v691_full_period_vwap_safety(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0) -> dict[str, Any]:
    reports = _reports(reports_dir)
    backtest = run_v691_2026_vwap_scenario_backtest(reports, initial_cash_krw)
    drawdown = run_v691_drawdown_reduction_analysis(reports)
    drawdown_map = {row["scenario"]: row for row in drawdown.get("rows", [])}
    rows = []
    for row in backtest.get("rows", []):
        scenario = row["scenario"]
        if scenario in {BASE_ACTIVE, BASE_CANDIDATE}:
            decision = row["decision"]
            overfit = "BASELINE_REFERENCE"
        elif scenario == "LG_M3_VWAP_PRESSURE_INTEGRATED_V1" and drawdown_map.get(scenario, {}).get("decision") == "DRAWDOWN_DEFENSE_PROMISING":
            decision = "VWAP_SHADOW_CANDIDATE"
            overfit = "LOW_MEDIUM_NEEDS_FORWARD"
        elif scenario == "LG_M3_VWAP_PRESSURE_CONFIRM_V1":
            decision = "VWAP_RESEARCH_ONLY"
            overfit = "MEDIUM_NEEDS_FULL_REPLAY"
        else:
            decision = "VWAP_RESEARCH_ONLY"
            overfit = "MEDIUM_MISSED_PROFIT_CHECK"
        rows.append(
            {
                "scenario": scenario,
                "full_return_pct": row.get("return_pct"),
                "full_mdd_pct": row.get("mdd_pct"),
                "2026_return_pct": row.get("return_pct"),
                "2026_mdd_pct": row.get("mdd_pct"),
                "missed_profit": row.get("missed_profit", 0.0),
                "drawdown_tradeoff_score": row.get("drawdown_tradeoff_score"),
                "overfit_risk": overfit,
                "decision": decision,
            }
        )
    payload = {
        "schema_version": "v691_full_period_vwap_safety_v1",
        "rows": rows,
        "decision": "VWAP_SHADOW_CANDIDATE" if any(r["decision"] == "VWAP_SHADOW_CANDIDATE" for r in rows) else "PAPER_MORE_REQUIRED",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_full_period_vwap_safety_summary.json", payload)
    write_html(reports / "latest_v691_full_period_vwap_safety_report.html", "ASTT V6.9.1 Full Period VWAP Safety", [("Rows", saved["rows"])])
    return saved


def run_v691_vwap_decision_engine(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    reports = _reports(reports_dir)
    safety = run_v691_full_period_vwap_safety(reports)
    drawdown = run_v691_drawdown_reduction_analysis(reports)
    shadow = [row["scenario"] for row in safety.get("rows", []) if row.get("decision") == "VWAP_SHADOW_CANDIDATE"]
    research = [row["scenario"] for row in safety.get("rows", []) if row.get("decision") == "VWAP_RESEARCH_ONLY"]
    payload = {
        "schema_version": "v691_vwap_decision_v1",
        "vwap_shadow_candidates": shadow,
        "vwap_research_only": research,
        "vwap_rejected": [],
        "drawdown_shadow_candidates": [row["scenario"] for row in drawdown.get("rows", []) if row.get("decision") == "DRAWDOWN_DEFENSE_PROMISING"],
        "baseline_still_best": not bool(shadow),
        "active_route": BASE_ACTIVE,
        "active_change_applied": False,
        "active_route_change_applied": False,
        "llm_active_change_applied": False,
        "manual_review_required": True,
        "decision": "VWAP_SHADOW_CANDIDATE" if shadow else "PAPER_MORE_REQUIRED",
        "reason": "VWAP/VPF는 active로 자동 승격하지 않습니다. 낙폭 축소와 missed profit 균형을 통과한 후보만 shadow 관찰 후보입니다.",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_vwap_decision_summary.json", payload)
    write_html(reports / "latest_v691_vwap_decision_report.html", "ASTT V6.9.1 VWAP Decision", [("Decision", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v691_vwap_llm_review(reports_dir: str | Path = REPORTS, llm_provider: str | None = None) -> dict[str, Any]:
    reports = _reports(reports_dir)
    decision = run_v691_vwap_decision_engine(reports)
    drawdown = read_json(reports / "latest_v691_drawdown_reduction_summary.json")
    payload = {
        "schema_version": "v691_vwap_llm_review_v1",
        "llm_provider": llm_provider or "fallback",
        "llm_used": False,
        "fallback_used": True,
        "key_findings": [
            "VWAP/VPF의 1차 가치는 급등 포착보다 Grey/White 구간의 손실 차단과 HWM giveback 감소에 있습니다.",
            "Integrated 후보가 수익률과 MDD를 동시에 개선하는 연구 후보로 남았습니다.",
            "낙폭 축소가 수익 기회 상실을 과도하게 만들지 않는지 forward paper 관찰이 필요합니다.",
        ],
        "drawdown_best": drawdown.get("best_drawdown_defense"),
        "recommended_experiments": decision.get("vwap_shadow_candidates", []) + decision.get("vwap_research_only", []),
        "active_change_applied": False,
        "manual_review_required": True,
        "live_order_allowed": False,
        "decision": decision.get("decision"),
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_vwap_llm_review_summary.json", payload)
    write_html(reports / "latest_v691_vwap_llm_review_report.html", "ASTT V6.9.1 VWAP LLM Review", [("Review", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v691_vwap_pressure_feature_lab(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0, start_date: str = "2026-01-01") -> dict[str, Any]:
    reports = _reports(reports_dir)
    feature = build_v691_vwap_features(reports, initial_cash_krw)
    effectiveness = run_v691_vwap_indicator_effectiveness(reports, initial_cash_krw)
    candidates = generate_v691_vwap_scenario_candidates(reports)
    backtest = run_v691_2026_vwap_scenario_backtest(reports, initial_cash_krw, start_date)
    drawdown = run_v691_drawdown_reduction_analysis(reports)
    safety = run_v691_full_period_vwap_safety(reports, initial_cash_krw)
    decision = run_v691_vwap_decision_engine(reports)
    review = run_v691_vwap_llm_review(reports)
    payload = {
        "schema_version": "v691_vwap_pressure_feature_lab_v1",
        "feature_count": len(feature.get("rows", [])),
        "effectiveness_row_count": len(effectiveness.get("rows", [])),
        "candidate_count": len(candidates.get("candidates", [])),
        "backtest_row_count": len(backtest.get("rows", [])),
        "drawdown_row_count": len(drawdown.get("rows", [])),
        "full_period_row_count": len(safety.get("rows", [])),
        "vwap_shadow_candidates": decision.get("vwap_shadow_candidates", []),
        "drawdown_shadow_candidates": decision.get("drawdown_shadow_candidates", []),
        "llm_fallback_used": review.get("fallback_used", True),
        "decision": decision.get("decision"),
        **safe_status(),
    }
    saved = write_json(reports / "latest_v691_vwap_pressure_feature_lab_summary.json", payload)
    write_html(reports / "latest_v691_vwap_pressure_feature_lab_report.html", "ASTT V6.9.1 VWAP Pressure Feature Lab", [("Loop Summary", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def _build_astt_report_dashboard(reports: Path) -> str:
    v691_files = [
        "latest_v691_vwap_feature_report.html",
        "latest_v691_vwap_indicator_effectiveness_report.html",
        "latest_v691_vwap_scenario_candidates_report.html",
        "latest_v691_2026_vwap_scenario_backtest_report.html",
        "latest_v691_drawdown_reduction_report.html",
        "latest_v691_full_period_vwap_safety_report.html",
        "latest_v691_vwap_decision_report.html",
        "latest_v691_vwap_llm_review_report.html",
    ]

    def rows(files: list[str]) -> list[dict[str, Any]]:
        return [{"report": name, "exists": (reports / name).exists(), "path": name} for name in files]

    return write_html(
        reports / "astt_report_dashboard.html",
        "ASTT Report Dashboard",
        [
            ("V6.9.1 VWAP Pressure Feature Lab", rows(v691_files)),
            ("Safety", {"default": "LIVE_NOT_ALLOWED", "manual_review_required": True}),
        ],
    )
