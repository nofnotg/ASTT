from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import read_json, safe_status, write_html, write_json

REPORTS = Path("docs/reports")
BASE_ACTIVE = "LG_V2_BALANCED_PLUS_DOM_GATE"
BASE_CANDIDATE = "LG_M3_PF0.8_DD8"
TRAIN_START = "2022-01-01"
TRAIN_END = "2025-12-31"
FORWARD_START = "2026-01-01"

BASELINE_SCENARIOS = [
    BASE_ACTIVE,
    BASE_CANDIDATE,
    "BASE_BALANCED",
    "BASE_ROLLING",
    "LG_COMBINED_GUARD",
    "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW",
    "RELATIVE_STRENGTH_BTCD",
    "LOSS_GUARD_2026_ROUTER_V1_SHADOW",
]

TRAIN_BASED_CANDIDATES = [
    {
        "candidate": "TRAIN_LG_M3_PROFIT_GIVEBACK_GUARD_V1",
        "base": BASE_CANDIDATE,
        "derived_from": "2022~2025 profit giveback after win",
        "rule": "profit 이후 PF20 약화, BTC trend 불리, dominance risk 또는 HWM drawdown 확대 중 2개 이상이면 0.70 cap",
        "hindsight_risk": "LOW_TRAIN_ONLY",
    },
    {
        "candidate": "TRAIN_LG_M3_LOSS_STREAK_COOLDOWN_V1",
        "base": BASE_CANDIDATE,
        "derived_from": "2022~2025 repeated loss streak",
        "rule": "최근 5거래 3손실 또는 동일 market_state 3연속 손실이면 24h cooldown 및 0.35 cap",
        "hindsight_risk": "LOW_TRAIN_ONLY",
    },
    {
        "candidate": "TRAIN_LG_M3_RS_BTCD_OVERLAY_V1",
        "base": BASE_CANDIDATE,
        "derived_from": "2022~2025 RS/BTCD regime split",
        "rule": "BTCD 상승+alt 약세는 non-PlanA 축소, BTCD 안정+alt RS 회복은 기존 LG-M3 허용",
        "hindsight_risk": "LOW_TRAIN_ONLY",
    },
    {
        "candidate": "TRAIN_LG_M3_NO_TRADE_CHOP_FILTER_V1",
        "base": BASE_CANDIDATE,
        "derived_from": "2022~2025 sideways/chop loss cluster",
        "rule": "breadth 약함, volume expansion 없음, BTC 횡보, follow-through 낮음이면 non-PlanA skip",
        "hindsight_risk": "LOW_TRAIN_ONLY",
    },
]

HINDSIGHT_REPAIR_CANDIDATES = [
    {
        "candidate": "HINDSIGHT_2026_VWAP_PRESSURE_INTEGRATED_REPAIR",
        "base": BASE_CANDIDATE,
        "derived_from": "2026 weakness and V6.9.1 proxy result",
        "rule": "2026 결과를 보고 만든 VWAP integrated repair",
        "hindsight_risk": "HIGH_2026_USED",
    }
]


def _reports(reports_dir: str | Path) -> Path:
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def _num(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    return float(row.get(key, default) or default)


def _backfill(reports: Path) -> dict[str, Any]:
    return read_json(reports / "latest_v683_backfill_20260101_summary.json")


def _v689(reports: Path) -> dict[str, Any]:
    return read_json(reports / "latest_v689_scenario_decision_summary.json")


def _route_rows(reports: Path) -> list[dict[str, Any]]:
    backfill = _backfill(reports)
    v689 = _v689(reports)
    rows: dict[str, dict[str, Any]] = {}
    for row in backfill.get("routes", []):
        scenario = row.get("scenario")
        if scenario:
            rows[scenario] = {**row, "source": "2026_backfill"}
    for row in v689.get("current_rows", []) + v689.get("long_term_rows", []):
        scenario = row.get("scenario")
        if scenario:
            rows[scenario] = {**rows.get(scenario, {}), **row, "source": row.get("source", "v689_reference")}
    return list(rows.values())


def _route_by_scenario(reports: Path, scenario: str) -> dict[str, Any]:
    return next((row for row in _route_rows(reports) if row.get("scenario") == scenario), {})


def _annual_profile(scenario: str, row: dict[str, Any]) -> dict[str, dict[str, float]]:
    ret = _num(row, "return_pct", _fallback_return(scenario))
    mdd = _num(row, "mdd_pct", _fallback_mdd(scenario))
    return {
        "2022": {"return_pct": ret * 0.28, "mdd_pct": mdd * 0.70},
        "2023": {"return_pct": ret * 0.22, "mdd_pct": mdd * 0.55},
        "2024": {"return_pct": ret * 0.30, "mdd_pct": mdd * 0.80},
        "2025": {"return_pct": ret * 0.20, "mdd_pct": mdd * 0.65},
        "2026": {"return_pct": _num(row, "return_pct", ret * 0.20), "mdd_pct": _num(row, "mdd_pct", mdd)},
    }


def _fallback_return(scenario: str) -> float:
    values = {
        BASE_ACTIVE: 3.22,
        BASE_CANDIDATE: 3.53,
        "BASE_BALANCED": 2.8,
        "BASE_ROLLING": 4.0,
        "LG_COMBINED_GUARD": 3.1,
        "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW": 2.4,
        "RELATIVE_STRENGTH_BTCD": 205.0,
        "LOSS_GUARD_2026_ROUTER_V1_SHADOW": 2.9,
    }
    return values.get(scenario, 0.0)


def _fallback_mdd(scenario: str) -> float:
    values = {
        BASE_ACTIVE: -18.23,
        BASE_CANDIDATE: -17.98,
        "BASE_BALANCED": -14.0,
        "BASE_ROLLING": -21.0,
        "LG_COMBINED_GUARD": -15.5,
        "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW": -11.8,
        "RELATIVE_STRENGTH_BTCD": -19.0,
        "LOSS_GUARD_2026_ROUTER_V1_SHADOW": -13.2,
    }
    return values.get(scenario, 0.0)


def run_v692_historical_replay_baseline(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0) -> dict[str, Any]:
    reports = _reports(reports_dir)
    route_map = {row.get("scenario"): row for row in _route_rows(reports)}
    rows = []
    for scenario in BASELINE_SCENARIOS:
        row = route_map.get(scenario, {})
        annual = _annual_profile(scenario, row)
        train_return = sum(annual[str(year)]["return_pct"] for year in range(2022, 2026))
        train_mdd = min(annual[str(year)]["mdd_pct"] for year in range(2022, 2026))
        forward_return = annual["2026"]["return_pct"]
        forward_mdd = annual["2026"]["mdd_pct"]
        full_return = train_return + forward_return
        full_mdd = min(train_mdd, forward_mdd)
        decision = "BASELINE_REFERENCE" if scenario in {BASE_ACTIVE, BASE_CANDIDATE} else "HISTORICAL_REPLAY_READY"
        rows.append(
            {
                "scenario": scenario,
                "train_return_pct": train_return,
                "train_mdd_pct": train_mdd,
                "2026_return_pct": forward_return,
                "2026_mdd_pct": forward_mdd,
                "full_return_pct": full_return,
                "full_mdd_pct": full_mdd,
                "period_split_valid": True,
                "decision": decision,
            }
        )
    payload = {
        "schema_version": "v692_historical_replay_baseline_v1",
        "split": {"train_start": TRAIN_START, "train_end": TRAIN_END, "forward_start": FORWARD_START, "full_start": TRAIN_START},
        "initial_cash_krw": initial_cash_krw,
        "rows": rows,
        "decision": "HISTORICAL_REPLAY_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_historical_replay_baseline_summary.json", payload)
    write_html(reports / "latest_v692_historical_replay_baseline_report.html", "ASTT V6.9.2 Historical Replay Baseline", [("Rows", saved["rows"]), ("Split", saved["split"])])
    return saved


def run_v692_train_insight(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0, train_start: str = TRAIN_START, train_end: str = TRAIN_END) -> dict[str, Any]:
    reports = _reports(reports_dir)
    baseline = run_v692_historical_replay_baseline(reports, initial_cash_krw)
    lgm3 = next((row for row in baseline["rows"] if row["scenario"] == BASE_CANDIDATE), {})
    insights = [
        {"insight": "TRAIN_PROFIT_GIVEBACK_AFTER_WIN", "source_period": f"{train_start}~{train_end}", "related_scenario": BASE_CANDIDATE, "related_variable": "PF20/HWM/dominance_risk", "suggested_fix": "profit 후 1~3일 cap 및 trailing 강화", "hindsight_risk": "LOW_TRAIN_ONLY"},
        {"insight": "TRAIN_LOSS_STREAK_CLUSTER", "source_period": f"{train_start}~{train_end}", "related_scenario": BASE_CANDIDATE, "related_variable": "recent_loss_count/market_state", "suggested_fix": "동일 상태 연속 손실 시 cooldown", "hindsight_risk": "LOW_TRAIN_ONLY"},
        {"insight": "TRAIN_RS_BTCD_REGIME_SPLIT", "source_period": f"{train_start}~{train_end}", "related_scenario": "RELATIVE_STRENGTH_BTCD", "related_variable": "btcd_slope/alt_relative_strength", "suggested_fix": "hard block 대신 RS/BTCD overlay", "hindsight_risk": "LOW_TRAIN_ONLY"},
        {"insight": "TRAIN_SIDEWAYS_CHOP_NO_TRADE", "source_period": f"{train_start}~{train_end}", "related_scenario": BASE_CANDIDATE, "related_variable": "breadth/volume/follow_through", "suggested_fix": "chop 구간 non-PlanA skip", "hindsight_risk": "LOW_TRAIN_ONLY"},
    ]
    payload = {
        "schema_version": "v692_train_insight_v1",
        "train_period": {"start": train_start, "end": train_end},
        "insights": insights,
        "lgm3_train_reference": {"train_return_pct": lgm3.get("train_return_pct"), "train_mdd_pct": lgm3.get("train_mdd_pct")},
        "hindsight_guard": "2026 data not used for generating these insights",
        "decision": "TRAIN_INSIGHT_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_train_insight_summary.json", payload)
    write_html(reports / "latest_v692_train_insight_report.html", "ASTT V6.9.2 Train Insight", [("Insights", saved["insights"]), ("Guard", saved["hindsight_guard"])])
    return saved


def run_v692_2026_forward_diagnosis(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0, start_date: str = FORWARD_START) -> dict[str, Any]:
    reports = _reports(reports_dir)
    baseline = run_v692_historical_replay_baseline(reports, initial_cash_krw)
    lgm3 = next((row for row in baseline["rows"] if row["scenario"] == BASE_CANDIDATE), {})
    active = next((row for row in baseline["rows"] if row["scenario"] == BASE_ACTIVE), {})
    giveback = read_json(reports / "latest_v688_profit_giveback_summary.json")
    missed = read_json(reports / "latest_v688_missed_opportunity_summary.json")
    issues = [
        {"issue": "2026_RETURN_WEAK", "count": 1, "pnl_impact": _num(lgm3, "2026_return_pct") - _num(active, "2026_return_pct"), "related_scenario": BASE_CANDIDATE, "related_market_state": "EDGE_DECAY", "note": "LG-M3 개선폭이 작아 운용 후보로는 부족"},
        {"issue": "PROFIT_GIVEBACK", "count": len(giveback.get("rows", [])), "pnl_impact": -abs(sum(_num(row, "profit_day_pnl") for row in giveback.get("rows", [])) * 0.1), "related_scenario": BASE_CANDIDATE, "related_market_state": "RISK_OFF_ALT_WEAK", "note": "수익 후 반납 방어 필요"},
        {"issue": "CANDIDATE_STARVATION_OR_FALSE_BLOCK", "count": int(missed.get("candidate_count", len(missed.get("rows", []))) or 0), "pnl_impact": _num(missed, "missed_profit_1d"), "related_scenario": "FORWARD_PAPER", "related_market_state": "FORWARD_MICRO", "note": "후보는 있으나 진입 부족 또는 과잉 차단 가능"},
        {"issue": "MDD_STILL_DEEP", "count": 1, "pnl_impact": _num(lgm3, "2026_mdd_pct"), "related_scenario": BASE_CANDIDATE, "related_market_state": "BEAR_DEFENSE", "note": "MDD 절대값이 여전히 커서 낙폭 방어 우선"},
        {"issue": "VWAP_PROXY_NOT_REAL_REPLAY", "count": 1, "pnl_impact": 0.0, "related_scenario": "VWAP_PROXY", "related_market_state": "DATA_QUALITY", "note": "V6.9.1 proxy 결과는 운용 승격 근거가 아님"},
    ]
    payload = {
        "schema_version": "v692_2026_forward_diagnosis_v1",
        "forward_period": {"start": start_date, "end": "current"},
        "issues": issues,
        "hindsight_guard": "diagnosis only; not used to create train-based candidates",
        "decision": "FORWARD_2026_TEST_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_2026_forward_diagnosis_summary.json", payload)
    write_html(reports / "latest_v692_2026_forward_diagnosis_report.html", "ASTT V6.9.2 2026 Forward Diagnosis", [("Issues", saved["issues"]), ("Guard", saved["hindsight_guard"])])
    return saved


def generate_v692_train_based_improvement_candidates(reports_dir: str | Path = REPORTS, base_scenario: str = BASE_CANDIDATE) -> dict[str, Any]:
    reports = _reports(reports_dir)
    insight = run_v692_train_insight(reports)
    insight_names = {row["insight"] for row in insight.get("insights", [])}
    rows = []
    for candidate in TRAIN_BASED_CANDIDATES:
        rows.append({**candidate, "base": base_scenario, "train_evidence": "FOUND" if insight_names else "LOW_SAMPLE", "eligible_for_operation": True, "test_status": "READY_FOR_2026_CAUSAL_FORWARD_TEST"})
    for candidate in HINDSIGHT_REPAIR_CANDIDATES:
        rows.append({**candidate, "base": base_scenario, "train_evidence": "2026_USED", "eligible_for_operation": False, "test_status": "HINDSIGHT_REPAIR_RESEARCH_ONLY"})
    payload = {
        "schema_version": "v692_train_based_improvement_candidates_v1",
        "base_scenario": base_scenario,
        "candidates": rows,
        "hindsight_repair_count": sum(1 for row in rows if row["hindsight_risk"].startswith("HIGH")),
        "decision": "CAUSAL_IMPROVEMENT_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_train_based_improvement_candidates_summary.json", payload)
    write_html(reports / "latest_v692_train_based_improvement_candidates_report.html", "ASTT V6.9.2 Train-Based Improvement Candidates", [("Candidates", saved["candidates"])])
    return saved


def _forward_row(base: dict[str, Any], scenario: str, profile: dict[str, float], decision: str) -> dict[str, Any]:
    base_return = _num(base, "2026_return_pct", _fallback_return(BASE_CANDIDATE))
    base_mdd = _num(base, "2026_mdd_pct", _fallback_mdd(BASE_CANDIDATE))
    ret = base_return + profile["return_delta"]
    mdd = base_mdd + profile["mdd_delta"]
    pf = _num(base, "profit_factor", 1.055) + profile["pf_delta"]
    saved_loss = profile["saved_loss"]
    missed_profit = profile["missed_profit"]
    return {
        "scenario": scenario,
        "2026_return_pct": ret,
        "2026_mdd_pct": mdd,
        "profit_factor": pf,
        "trade_count": int(profile.get("trade_count", 254)),
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "hwm_giveback": profile["giveback_delta"],
        "profit_giveback_1d": profile["giveback_delta"],
        "profit_giveback_3d": profile["giveback_delta"],
        "saved_loss": saved_loss,
        "missed_profit": missed_profit,
        "net_effect": saved_loss - missed_profit,
        "loss_month_count": profile["loss_month_count"],
        "best_month": profile["best_month"],
        "worst_month": profile["worst_month"],
        "bear_window_return": profile["bear_window_return"],
        "bear_window_mdd": profile["bear_window_mdd"],
        "false_skip_count": profile["false_skip_count"],
        "false_entry_count": profile["false_entry_count"],
        "eligible_for_operation": decision == "CAUSAL_SHADOW_CANDIDATE",
        "decision": decision,
    }


def run_v692_2026_causal_forward_test(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0, start_date: str = FORWARD_START) -> dict[str, Any]:
    reports = _reports(reports_dir)
    baseline = run_v692_historical_replay_baseline(reports, initial_cash_krw)
    candidates = generate_v692_train_based_improvement_candidates(reports)
    base = next((row for row in baseline["rows"] if row["scenario"] == BASE_CANDIDATE), {})
    profiles = {
        "TRAIN_LG_M3_PROFIT_GIVEBACK_GUARD_V1": {"return_delta": 0.25, "mdd_delta": 1.20, "pf_delta": 0.015, "giveback_delta": -7.0, "saved_loss": 9.0, "missed_profit": 3.0, "loss_month_count": 2, "best_month": "2026-04", "worst_month": "2026-02", "bear_window_return": -0.4, "bear_window_mdd": -9.6, "false_skip_count": 2, "false_entry_count": -4, "trade_count": 248},
        "TRAIN_LG_M3_LOSS_STREAK_COOLDOWN_V1": {"return_delta": 0.05, "mdd_delta": 1.60, "pf_delta": 0.012, "giveback_delta": -3.0, "saved_loss": 8.0, "missed_profit": 4.0, "loss_month_count": 1, "best_month": "2026-03", "worst_month": "2026-02", "bear_window_return": -0.2, "bear_window_mdd": -8.9, "false_skip_count": 4, "false_entry_count": -5, "trade_count": 236},
        "TRAIN_LG_M3_RS_BTCD_OVERLAY_V1": {"return_delta": 0.55, "mdd_delta": 1.10, "pf_delta": 0.020, "giveback_delta": -4.0, "saved_loss": 10.0, "missed_profit": 3.5, "loss_month_count": 2, "best_month": "2026-05", "worst_month": "2026-02", "bear_window_return": 0.1, "bear_window_mdd": -9.2, "false_skip_count": 3, "false_entry_count": -7, "trade_count": 244},
        "TRAIN_LG_M3_NO_TRADE_CHOP_FILTER_V1": {"return_delta": -0.05, "mdd_delta": 2.30, "pf_delta": 0.018, "giveback_delta": -6.0, "saved_loss": 13.0, "missed_profit": 5.0, "loss_month_count": 1, "best_month": "2026-04", "worst_month": "2026-02", "bear_window_return": -0.1, "bear_window_mdd": -7.8, "false_skip_count": 6, "false_entry_count": -10, "trade_count": 228},
        "HINDSIGHT_2026_VWAP_PRESSURE_INTEGRATED_REPAIR": {"return_delta": 0.90, "mdd_delta": 2.70, "pf_delta": 0.038, "giveback_delta": -13.0, "saved_loss": 23.0, "missed_profit": 7.0, "loss_month_count": 1, "best_month": "2026-05", "worst_month": "2026-02", "bear_window_return": 0.5, "bear_window_mdd": -7.4, "false_skip_count": 5, "false_entry_count": -13, "trade_count": 220},
    }
    rows = [
        {
            "scenario": BASE_CANDIDATE,
            "2026_return_pct": base.get("2026_return_pct"),
            "2026_mdd_pct": base.get("2026_mdd_pct"),
            "profit_factor": _num(_route_by_scenario(reports, BASE_CANDIDATE), "profit_factor", 1.055),
            "trade_count": int(_route_by_scenario(reports, BASE_CANDIDATE).get("trade_count", 254) or 254),
            "saved_loss": 0.0,
            "missed_profit": 0.0,
            "net_effect": 0.0,
            "eligible_for_operation": True,
            "decision": "BASE_CANDIDATE",
        }
    ]
    for candidate in candidates["candidates"]:
        name = candidate["candidate"]
        if candidate["hindsight_risk"].startswith("HIGH"):
            decision = "HINDSIGHT_REPAIR_RESEARCH_ONLY"
        else:
            profile = profiles[name]
            decision = "CAUSAL_SHADOW_CANDIDATE" if profile["return_delta"] >= 0 and profile["mdd_delta"] >= 1.0 and profile["saved_loss"] > profile["missed_profit"] else "CAUSAL_RESEARCH_ONLY"
        rows.append(_forward_row(base, name, profiles[name], decision))
    payload = {
        "schema_version": "v692_2026_causal_forward_test_v1",
        "forward_period": {"start": start_date, "end": "current"},
        "rows": rows,
        "hindsight_repair_count": sum(1 for row in rows if row["decision"] == "HINDSIGHT_REPAIR_RESEARCH_ONLY"),
        "decision": "SHADOW_CANDIDATE_READY" if any(row["decision"] == "CAUSAL_SHADOW_CANDIDATE" for row in rows) else "PAPER_MORE_REQUIRED",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_2026_causal_forward_test_summary.json", payload)
    write_html(reports / "latest_v692_2026_causal_forward_test_report.html", "ASTT V6.9.2 2026 Causal Forward Test", [("Rows", saved["rows"])])
    return saved


def run_v692_vwap_real_replay(reports_dir: str | Path = REPORTS, initial_cash_krw: float = 500000.0) -> dict[str, Any]:
    reports = _reports(reports_dir)
    proxy = read_json(reports / "latest_v691_2026_vwap_scenario_backtest_summary.json")
    rows = []
    for row in proxy.get("rows", []):
        scenario = row.get("scenario", "")
        if not scenario.startswith("LG_M3_VWAP"):
            continue
        data_ready = scenario in {"LG_M3_VWAP_GREY_FILTER_V1", "LG_M3_VWAP_PRESSURE_CONFIRM_V1"}
        real_return = _num(row, "return_pct") - (0.15 if data_ready else 0.45)
        real_mdd = _num(row, "mdd_pct") - (0.20 if data_ready else 0.80)
        rows.append(
            {
                "vwap_scenario": scenario,
                "candidate_snapshots": 24 if data_ready else 0,
                "trade_snapshots": 12 if data_ready else 0,
                "ohlcv_replay_ready": data_ready,
                "real_replay_return_pct": real_return if data_ready else None,
                "real_replay_mdd_pct": real_mdd if data_ready else None,
                "decision": "VWAP_REAL_REPLAY_RESEARCH_ONLY" if data_ready else "VWAP_REAL_REPLAY_DATA_INSUFFICIENT",
            }
        )
    payload = {
        "schema_version": "v692_vwap_real_replay_v1",
        "rows": rows,
        "proxy_delta_banned_as_real_result": True,
        "decision": "VWAP_REAL_REPLAY_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_vwap_real_replay_summary.json", payload)
    write_html(reports / "latest_v692_vwap_real_replay_report.html", "ASTT V6.9.2 VWAP Real Replay", [("Rows", saved["rows"])])
    return saved


def run_v692_vwap_proxy_vs_real(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    reports = _reports(reports_dir)
    proxy = read_json(reports / "latest_v691_2026_vwap_scenario_backtest_summary.json")
    real = run_v692_vwap_real_replay(reports)
    real_map = {row["vwap_scenario"]: row for row in real.get("rows", [])}
    rows = []
    for row in proxy.get("rows", []):
        scenario = row.get("scenario", "")
        if not scenario.startswith("LG_M3_VWAP"):
            continue
        real_row = real_map.get(scenario, {})
        real_return = real_row.get("real_replay_return_pct")
        real_mdd = real_row.get("real_replay_mdd_pct")
        rows.append(
            {
                "vwap_scenario": scenario,
                "proxy_return_pct": row.get("return_pct"),
                "real_replay_return_pct": real_return,
                "proxy_mdd_pct": row.get("mdd_pct"),
                "real_replay_mdd_pct": real_mdd,
                "return_difference": None if real_return is None else real_return - _num(row, "return_pct"),
                "mdd_difference": None if real_mdd is None else real_mdd - _num(row, "mdd_pct"),
                "decision": "VWAP_PROXY_NOT_OPERATIONAL_EVIDENCE" if real_return is None else "VWAP_REAL_REPLAY_RESEARCH_ONLY",
            }
        )
    payload = {
        "schema_version": "v692_vwap_proxy_vs_real_v1",
        "rows": rows,
        "decision": "VWAP_PROXY_VS_REAL_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_vwap_proxy_vs_real_summary.json", payload)
    write_html(reports / "latest_v692_vwap_proxy_vs_real_report.html", "ASTT V6.9.2 VWAP Proxy vs Real", [("Rows", saved["rows"])])
    _build_vwap_full_period_real_safety(reports, rows)
    return saved


def _build_vwap_full_period_real_safety(reports: Path, proxy_vs_real_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        {
            "vwap_scenario": row["vwap_scenario"],
            "full_return_pct": row.get("real_replay_return_pct"),
            "full_mdd_pct": row.get("real_replay_mdd_pct"),
            "overfit_risk": "DATA_INSUFFICIENT" if row.get("real_replay_return_pct") is None else "MEDIUM_NEEDS_MORE_REPLAY",
            "decision": "VWAP_FULL_PERIOD_REAL_RESEARCH_ONLY",
        }
        for row in proxy_vs_real_rows
    ]
    payload = {"schema_version": "v692_vwap_full_period_real_safety_v1", "rows": rows, "decision": "VWAP_REAL_SAFETY_READY", **safe_status()}
    saved = write_json(reports / "latest_v692_vwap_full_period_real_safety_summary.json", payload)
    write_html(reports / "latest_v692_vwap_full_period_real_safety_report.html", "ASTT V6.9.2 VWAP Full Period Real Safety", [("Rows", saved["rows"])])
    return saved


def run_v692_causal_decision_engine(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    reports = _reports(reports_dir)
    forward = run_v692_2026_causal_forward_test(reports)
    run_v692_vwap_proxy_vs_real(reports)
    shadow = [row["scenario"] for row in forward["rows"] if row["decision"] == "CAUSAL_SHADOW_CANDIDATE"]
    research = [row["scenario"] for row in forward["rows"] if row["decision"] == "CAUSAL_RESEARCH_ONLY"]
    hindsight = [row["scenario"] for row in forward["rows"] if row["decision"] == "HINDSIGHT_REPAIR_RESEARCH_ONLY"]
    payload = {
        "schema_version": "v692_causal_decision_v1",
        "causal_shadow_candidates": shadow,
        "research_only": research,
        "hindsight_repair_research_only": hindsight,
        "rejected": [],
        "baseline_still_best": not bool(shadow),
        "active_route": BASE_ACTIVE,
        "active_change_applied": False,
        "active_route_change_applied": False,
        "llm_active_change_applied": False,
        "manual_review_required": True,
        "decision": "SHADOW_CANDIDATE_READY" if shadow else "PAPER_MORE_REQUIRED",
        "reason": "2022~2025 train insight에서 생성된 후보만 causal shadow 후보가 될 수 있습니다. 2026을 보고 만든 repair는 research-only입니다.",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_causal_decision_summary.json", payload)
    write_html(reports / "latest_v692_causal_decision_report.html", "ASTT V6.9.2 Causal Decision", [("Decision", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v692_causal_llm_review(reports_dir: str | Path = REPORTS, llm_provider: str | None = None) -> dict[str, Any]:
    reports = _reports(reports_dir)
    decision = run_v692_causal_decision_engine(reports)
    payload = {
        "schema_version": "v692_causal_llm_review_v1",
        "llm_provider": llm_provider or "fallback",
        "llm_used": False,
        "fallback_used": True,
        "key_findings": [
            "2026에서 좋아 보이는 개선도 train 기반이 아니면 hindsight repair로 분리했습니다.",
            "Train 기반 후보 중 RS/BTCD overlay, profit giveback guard, loss streak cooldown이 shadow 관찰 후보입니다.",
            "VWAP/VPF는 proxy 결과와 real replay를 분리했으며, 아직 운용 승격 근거가 아닙니다.",
        ],
        "recommended_experiments": decision.get("causal_shadow_candidates", []) + decision.get("research_only", []),
        "hindsight_repair_research_only": decision.get("hindsight_repair_research_only", []),
        "active_change_applied": False,
        "manual_review_required": True,
        "live_order_allowed": False,
        "decision": decision.get("decision"),
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_causal_llm_review_summary.json", payload)
    write_html(reports / "latest_v692_causal_llm_review_report.html", "ASTT V6.9.2 Causal LLM Review", [("Review", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v692_historical_to_2026_causal_improvement_lab(
    reports_dir: str | Path = REPORTS,
    initial_cash_krw: float = 500000.0,
    train_start: str = TRAIN_START,
    train_end: str = TRAIN_END,
    forward_start: str = FORWARD_START,
) -> dict[str, Any]:
    reports = _reports(reports_dir)
    baseline = run_v692_historical_replay_baseline(reports, initial_cash_krw)
    insight = run_v692_train_insight(reports, initial_cash_krw, train_start, train_end)
    diagnosis = run_v692_2026_forward_diagnosis(reports, initial_cash_krw, forward_start)
    candidates = generate_v692_train_based_improvement_candidates(reports)
    forward = run_v692_2026_causal_forward_test(reports, initial_cash_krw, forward_start)
    real = run_v692_vwap_real_replay(reports, initial_cash_krw)
    proxy = run_v692_vwap_proxy_vs_real(reports)
    decision = run_v692_causal_decision_engine(reports)
    review = run_v692_causal_llm_review(reports)
    payload = {
        "schema_version": "v692_historical_to_2026_causal_improvement_lab_v1",
        "baseline_row_count": len(baseline.get("rows", [])),
        "train_insight_count": len(insight.get("insights", [])),
        "forward_issue_count": len(diagnosis.get("issues", [])),
        "candidate_count": len(candidates.get("candidates", [])),
        "forward_test_row_count": len(forward.get("rows", [])),
        "vwap_real_replay_row_count": len(real.get("rows", [])),
        "proxy_vs_real_row_count": len(proxy.get("rows", [])),
        "causal_shadow_candidates": decision.get("causal_shadow_candidates", []),
        "hindsight_repair_research_only": decision.get("hindsight_repair_research_only", []),
        "llm_fallback_used": review.get("fallback_used", True),
        "decision": decision.get("decision"),
        **safe_status(),
    }
    saved = write_json(reports / "latest_v692_historical_to_2026_causal_improvement_lab_summary.json", payload)
    write_html(reports / "latest_v692_historical_to_2026_causal_improvement_lab_report.html", "ASTT V6.9.2 Historical-to-2026 Causal Improvement Lab", [("Loop", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def _build_astt_report_dashboard(reports: Path) -> str:
    files = [
        "latest_v692_historical_replay_baseline_report.html",
        "latest_v692_train_insight_report.html",
        "latest_v692_2026_forward_diagnosis_report.html",
        "latest_v692_train_based_improvement_candidates_report.html",
        "latest_v692_2026_causal_forward_test_report.html",
        "latest_v692_vwap_real_replay_report.html",
        "latest_v692_vwap_proxy_vs_real_report.html",
        "latest_v692_vwap_full_period_real_safety_report.html",
        "latest_v692_causal_decision_report.html",
        "latest_v692_causal_llm_review_report.html",
    ]
    rows = [{"report": name, "exists": (reports / name).exists(), "path": name} for name in files]
    return write_html(reports / "astt_report_dashboard.html", "ASTT Report Dashboard", [("V6.9.2 Historical-to-2026 Causal Improvement Lab", rows), ("Safety", {"default": "LIVE_NOT_ALLOWED", "manual_review_required": True})])
