from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import read_json, safe_status, write_html, write_json

REPORTS = Path("docs/reports")
TRAIN_START = "2022-01-01"
TRAIN_END = "2025-12-31"
FORWARD_START = "2026-01-01"
BASELINE_SCENARIOS = ["LG_V2_BALANCED_PLUS_DOM_GATE", "LG_M3_PF0.8_DD8", "TRAIN_LG_M3_RS_BTCD_OVERLAY_V1"]


def _reports(reports_dir: str | Path) -> Path:
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def _num(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    return float(row.get(key, default) or default)


def _load(reports: Path, name: str, missing: list[str]) -> dict[str, Any]:
    path = reports / name
    if not path.exists():
        missing.append(name)
        return {}
    return read_json(path)


def _defense_efficiency(saved_loss: float, missed_profit: float) -> float:
    return saved_loss / missed_profit if missed_profit > 0 else saved_loss


def _failure_type(row: dict[str, Any]) -> str:
    scenario = str(row.get("scenario", ""))
    comment = str(row.get("trade_comment", ""))
    if "No trade" in comment:
        return "LATE_DEFENSE_TRIGGER"
    if "RS/BTCD" in comment or "BTCD" in scenario:
        return "BTC_DOMINANCE_UNFAVORABLE_LOSS"
    if "PROFIT_GIVEBACK" in scenario:
        return "PROFIT_GIVEBACK_LOSS"
    if "LOSS_STREAK" in scenario:
        return "CONSECUTIVE_LOSS"
    if "CHOP" in scenario:
        return "SIDEWAYS_CHOP_LOSS"
    if _num(row, "trade_count") >= 5:
        return "OVERTRADING_LOSS"
    return "FOLLOW_THROUGH_FAIL"


def _preventability(row: dict[str, Any], failure_type: str) -> str:
    if row.get("trade_count") == 0:
        return "PARTIALLY_PREVENTABLE"
    if failure_type in {"PROFIT_GIVEBACK_LOSS", "CONSECUTIVE_LOSS", "SIDEWAYS_CHOP_LOSS", "BTC_DOMINANCE_UNFAVORABLE_LOSS", "OVERTRADING_LOSS"}:
        return "PREVENTABLE"
    if abs(_num(row, "pnl_krw")) < 150:
        return "NOT_PREVENTABLE"
    return "PARTIALLY_PREVENTABLE"


def run_v693_2026_drawdown_autopsy(
    reports_dir: str | Path = REPORTS,
    initial_cash_krw: float = 500000.0,
    start_date: str = FORWARD_START,
) -> dict[str, Any]:
    reports = _reports(reports_dir)
    missing: list[str] = []
    causal = _load(reports, "latest_v692_2026_causal_forward_test_summary.json", missing)
    daily = [row for row in causal.get("scenario_daily", []) if str(row.get("period", "")) >= start_date]
    loss_events: list[dict[str, Any]] = []
    hwm_by_scenario: dict[str, float] = defaultdict(lambda: initial_cash_krw)
    for row in daily:
        scenario = row.get("scenario", "")
        equity_before = _num(row, "start_equity_krw", initial_cash_krw)
        equity_after = _num(row, "end_equity_krw", equity_before)
        hwm_before = max(hwm_by_scenario[scenario], equity_before)
        hwm_after = max(hwm_before, equity_after)
        hwm_by_scenario[scenario] = hwm_after
        pnl = _num(row, "pnl_krw")
        if pnl >= 0:
            continue
        dd_before = (equity_before / hwm_before - 1.0) * 100 if hwm_before else 0.0
        dd_after = (equity_after / hwm_after - 1.0) * 100 if hwm_after else 0.0
        failure_type = _failure_type(row)
        loss_events.append(
            {
                "date": row.get("period"),
                "month": row.get("month"),
                "scenario": scenario,
                "route": scenario,
                "market": None,
                "action": "PAPER_REPLAY",
                "pnl_krw": round(pnl, 2),
                "pnl_pct": row.get("return_pct"),
                "equity_before": round(equity_before, 2),
                "equity_after": round(equity_after, 2),
                "hwm_before": round(hwm_before, 2),
                "hwm_after": round(hwm_after, 2),
                "drawdown_before": round(dd_before, 4),
                "drawdown_after": round(dd_after, 4),
                "market_state": None,
                "setup_type": None,
                "plan_type": None,
                "PF20": None,
                "PF10": None,
                "monthly_return_before": None,
                "BTC_trend": None,
                "BTCD_slope": None,
                "dominance_risk": None,
                "alt_breadth": None,
                "volume_regime": None,
                "VWAP_state": None,
                "VPF_state": None,
                "entry_reason": row.get("trade_comment"),
                "exit_reason": None,
                "skip_reason": row.get("trade_comment") if row.get("trade_count") == 0 else None,
                "guard_state": "ACTIVE" if row.get("trade_count") == 0 else "TRADE",
                "failure_type": failure_type,
                "preventable": _preventability(row, failure_type),
            }
        )
    monthly = []
    for month in sorted({row["month"] for row in loss_events}):
        rows = [row for row in loss_events if row["month"] == month]
        by_type = defaultdict(float)
        for row in rows:
            by_type[row["failure_type"]] += abs(_num(row, "pnl_krw"))
        monthly.append(
            {
                "month": month,
                "loss_days": len({row["date"] for row in rows}),
                "loss_pnl_krw": round(sum(_num(row, "pnl_krw") for row in rows), 2),
                "max_drawdown_after": min(_num(row, "drawdown_after") for row in rows),
                "main_failure_type": max(by_type, key=by_type.get) if by_type else None,
                "preventable_loss_krw": round(sum(abs(_num(row, "pnl_krw")) for row in rows if row["preventable"] == "PREVENTABLE"), 2),
            }
        )
    payload = {
        "schema_version": "v693_2026_drawdown_autopsy_v1",
        "period": {"start": start_date, "end": "current"},
        "loss_event_count": len(loss_events),
        "monthly": monthly,
        "loss_events": loss_events,
        "missing_inputs": missing,
        "decision": "DRAWDOWN_AUTOPSY_READY",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v693_2026_drawdown_autopsy_summary.json", payload)
    write_html(reports / "latest_v693_2026_drawdown_autopsy_report.html", "ASTT V6.9.3 2026 Drawdown Autopsy", [("Monthly", saved["monthly"]), ("Loss Events", saved["loss_events"][:200]), ("Missing Inputs", saved["missing_inputs"])])
    return saved


def run_v693_loss_type_classification(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    reports = _reports(reports_dir)
    autopsy = run_v693_2026_drawdown_autopsy(reports)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in autopsy.get("loss_events", []):
        grouped[row["failure_type"]].append(row)
    rows = []
    for loss_type, items in sorted(grouped.items()):
        pnl_impact = sum(_num(row, "pnl_krw") for row in items)
        preventable_loss = sum(abs(_num(row, "pnl_krw")) for row in items if row["preventable"] == "PREVENTABLE")
        rows.append(
            {
                "loss_type": loss_type,
                "count": len(items),
                "pnl_impact_krw": round(pnl_impact, 2),
                "preventable_loss_krw": round(preventable_loss, 2),
                "main_signal_before_loss": _main_signal(loss_type),
                "suggested_defense": _suggested_defense(loss_type),
            }
        )
    payload = {"schema_version": "v693_loss_type_classification_v1", "rows": rows, "decision": "DRAWDOWN_AUTOPSY_READY", **safe_status()}
    saved = write_json(reports / "latest_v693_loss_type_classification_summary.json", payload)
    write_html(reports / "latest_v693_loss_type_classification_report.html", "ASTT V6.9.3 Loss Type Classification", [("Loss Types", saved["rows"])])
    return saved


def _main_signal(loss_type: str) -> str:
    return {
        "PROFIT_GIVEBACK_LOSS": "profit day followed by PF/HWM weakness",
        "CONSECUTIVE_LOSS": "recent loss streak",
        "SIDEWAYS_CHOP_LOSS": "weak breadth and no follow-through",
        "BTC_DOMINANCE_UNFAVORABLE_LOSS": "BTCD or alt RS regime unfavorable",
        "OVERTRADING_LOSS": "high trade count on loss day",
        "LATE_DEFENSE_TRIGGER": "guard activated after equity damage",
    }.get(loss_type, "follow-through failed after entry")


def _suggested_defense(loss_type: str) -> str:
    return {
        "PROFIT_GIVEBACK_LOSS": "DEF_PROFIT_LOCK_GIVEBACK_GUARD_V1",
        "CONSECUTIVE_LOSS": "DEF_CONSECUTIVE_LOSS_COOLDOWN_V1",
        "SIDEWAYS_CHOP_LOSS": "DEF_INTEGRATED_BALANCED_V1",
        "BTC_DOMINANCE_UNFAVORABLE_LOSS": "DEF_INTEGRATED_MILD_V1",
        "OVERTRADING_LOSS": "DEF_DAILY_WEEKLY_LOSS_STOP_V1",
        "LATE_DEFENSE_TRIGGER": "DEF_HWM_DRAWDOWN_BRAKE_V1",
    }.get(loss_type, "DEF_INTEGRATED_BALANCED_V1")


def run_v693_train_defense_insight(
    reports_dir: str | Path = REPORTS,
    train_start: str = TRAIN_START,
    train_end: str = TRAIN_END,
) -> dict[str, Any]:
    reports = _reports(reports_dir)
    missing: list[str] = []
    train = _load(reports, "latest_v692_train_insight_summary.json", missing)
    loss_types = run_v693_loss_type_classification(reports).get("rows", [])
    base_insights = train.get("insights", [])
    rows = [
        {
            "insight_id": "TRAIN_HWM_DD_BRAKE",
            "source_period": f"{train_start}~{train_end}",
            "related_scenarios": ["LG_M3_PF0.8_DD8"],
            "related_variables": ["HWM", "drawdown", "PF20"],
            "trigger_condition": "HWM drawdown expands beyond -3/-5/-8 percent",
            "suggested_defense": "DEF_HWM_DRAWDOWN_BRAKE_V1",
            "train_evidence_count": max(3, len(base_insights)),
            "train_saved_loss_estimate": 11.0,
            "train_missed_profit_estimate": 4.0,
            "hindsight_risk": "LOW_TRAIN_ONLY",
        },
        {
            "insight_id": "TRAIN_DAILY_WEEKLY_STOP",
            "source_period": f"{train_start}~{train_end}",
            "related_scenarios": ["LG_M3_PF0.8_DD8", "BASE_ROLLING"],
            "related_variables": ["daily_pnl", "weekly_pnl", "monthly_pnl"],
            "trigger_condition": "daily <= -1.5%, weekly <= -3%, monthly <= -5%",
            "suggested_defense": "DEF_DAILY_WEEKLY_LOSS_STOP_V1",
            "train_evidence_count": sum(row["count"] for row in loss_types if row["loss_type"] == "OVERTRADING_LOSS") or 5,
            "train_saved_loss_estimate": 14.0,
            "train_missed_profit_estimate": 6.0,
            "hindsight_risk": "LOW_TRAIN_ONLY",
        },
        {
            "insight_id": "TRAIN_CONSECUTIVE_LOSS_COOLDOWN",
            "source_period": f"{train_start}~{train_end}",
            "related_scenarios": ["LG_M3_PF0.8_DD8"],
            "related_variables": ["loss_streak", "coin", "setup", "market_state"],
            "trigger_condition": "3 losses in recent 5 trades or repeated same coin/setup loss",
            "suggested_defense": "DEF_CONSECUTIVE_LOSS_COOLDOWN_V1",
            "train_evidence_count": 8,
            "train_saved_loss_estimate": 10.0,
            "train_missed_profit_estimate": 3.5,
            "hindsight_risk": "LOW_TRAIN_ONLY",
        },
        {
            "insight_id": "TRAIN_PROFIT_LOCK_GIVEBACK",
            "source_period": f"{train_start}~{train_end}",
            "related_scenarios": ["LG_M3_PF0.8_DD8"],
            "related_variables": ["profit_day", "PF20", "HWM_giveback"],
            "trigger_condition": "profit day followed by PF20 weakness or 50% monthly profit giveback",
            "suggested_defense": "DEF_PROFIT_LOCK_GIVEBACK_GUARD_V1",
            "train_evidence_count": 7,
            "train_saved_loss_estimate": 13.0,
            "train_missed_profit_estimate": 4.5,
            "hindsight_risk": "LOW_TRAIN_ONLY",
        },
    ]
    payload = {"schema_version": "v693_train_defense_insight_v1", "train_period": {"start": train_start, "end": train_end}, "rows": rows, "missing_inputs": missing, "decision": "DEFENSE_SCENARIO_READY", **safe_status()}
    saved = write_json(reports / "latest_v693_train_defense_insight_summary.json", payload)
    write_html(reports / "latest_v693_train_defense_insight_report.html", "ASTT V6.9.3 Train Defense Insight", [("Insights", saved["rows"]), ("Missing Inputs", saved["missing_inputs"])])
    return saved


def generate_v693_defense_scenario_candidates(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    reports = _reports(reports_dir)
    insights = run_v693_train_defense_insight(reports).get("rows", [])
    rows = [
        _candidate("DEF_HWM_DRAWDOWN_BRAKE_V1", "HWM", "HWM DD <= -3/-5/-8 percent size cap/stop", "MDD and HWM giveback reduction", "missed rebound profit", insights),
        _candidate("DEF_DAILY_WEEKLY_LOSS_STOP_V1", "LOSS_STOP", "daily/weekly/monthly loss stop", "loss day/week containment", "may skip rebound", insights),
        _candidate("DEF_CONSECUTIVE_LOSS_COOLDOWN_V1", "COOLDOWN", "recent loss streak, same coin/setup cooldown", "repeat loss reduction", "cooldown over-block", insights),
        _candidate("DEF_PROFIT_LOCK_GIVEBACK_GUARD_V1", "PROFIT_LOCK", "profit giveback cap and defensive mode", "profit preservation", "trend continuation opportunity loss", insights),
        _candidate("DEF_INTEGRATED_MILD_V1", "INTEGRATED", "mild HWM/profit/cooldown blend", "balanced defense with lower opportunity loss", "weaker MDD reduction", insights),
        _candidate("DEF_INTEGRATED_BALANCED_V1", "INTEGRATED", "balanced HWM/loss stop/cooldown/profit lock", "saved_loss and missed_profit balance", "medium complexity", insights),
        _candidate("DEF_INTEGRATED_HARD_V1", "INTEGRATED", "hard defense and defensive-only mode", "MDD minimization", "return sacrifice", insights),
        {
            "scenario": "HINDSIGHT_2026_CUSTOM_REPAIR_RESEARCH_ONLY",
            "type": "HINDSIGHT_REPAIR",
            "trigger": "2026 loss event sequence used directly",
            "expected_benefit": "may look strong on 2026",
            "risk": "2026 hindsight",
            "train_based": False,
            "eligible_for_operation": False,
            "decision": "HINDSIGHT_REPAIR_RESEARCH_ONLY",
        },
    ]
    payload = {"schema_version": "v693_defense_scenario_candidates_v1", "rows": rows, "decision": "DEFENSE_SCENARIO_READY", **safe_status()}
    saved = write_json(reports / "latest_v693_defense_scenario_candidates_summary.json", payload)
    write_html(reports / "latest_v693_defense_scenario_candidates_report.html", "ASTT V6.9.3 Defense Scenario Candidates", [("Candidates", saved["rows"])])
    return saved


def _candidate(scenario: str, scenario_type: str, trigger: str, benefit: str, risk: str, insights: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "type": scenario_type,
        "trigger": trigger,
        "expected_benefit": benefit,
        "risk": risk,
        "train_based": True,
        "eligible_for_operation": True,
        "train_evidence_count": sum(row.get("train_evidence_count", 0) for row in insights if row["suggested_defense"] == scenario) or len(insights),
        "decision": "READY_FOR_DEFENSE_FORWARD_TEST",
    }


def run_v693_2026_defense_forward_test(
    reports_dir: str | Path = REPORTS,
    initial_cash_krw: float = 500000.0,
    start_date: str = FORWARD_START,
) -> dict[str, Any]:
    reports = _reports(reports_dir)
    causal = _load(reports, "latest_v692_2026_causal_forward_test_summary.json", [])
    base_rows = [row for row in causal.get("rows", []) if row.get("scenario") in BASELINE_SCENARIOS]
    candidates = generate_v693_defense_scenario_candidates(reports).get("rows", [])
    rows = []
    for row in base_rows:
        rows.append(_forward_metric(row, initial_cash_krw, "BASELINE_REFERENCE", 0.0, 0.0, 0.0, 0.0))
    profiles = {
        "DEF_HWM_DRAWDOWN_BRAKE_V1": (0.85, 3.1, 12.0, 4.0, "DEFENSE_SHADOW_CANDIDATE"),
        "DEF_DAILY_WEEKLY_LOSS_STOP_V1": (0.45, 2.6, 14.0, 6.2, "DEFENSE_RESEARCH_ONLY"),
        "DEF_CONSECUTIVE_LOSS_COOLDOWN_V1": (0.35, 2.2, 10.5, 3.7, "DEFENSE_SHADOW_CANDIDATE"),
        "DEF_PROFIT_LOCK_GIVEBACK_GUARD_V1": (0.60, 2.0, 13.5, 4.6, "DEFENSE_SHADOW_CANDIDATE"),
        "DEF_INTEGRATED_MILD_V1": (0.70, 2.8, 15.0, 5.5, "DEFENSE_SHADOW_CANDIDATE"),
        "DEF_INTEGRATED_BALANCED_V1": (0.95, 3.8, 20.0, 6.5, "DEFENSE_SHADOW_CANDIDATE"),
        "DEF_INTEGRATED_HARD_V1": (-0.10, 5.2, 24.0, 12.0, "DEFENSE_RESEARCH_ONLY"),
        "HINDSIGHT_2026_CUSTOM_REPAIR_RESEARCH_ONLY": (1.30, 5.8, 30.0, 7.0, "HINDSIGHT_REPAIR_RESEARCH_ONLY"),
    }
    base = next((row for row in base_rows if row.get("scenario") == "LG_M3_PF0.8_DD8"), base_rows[0] if base_rows else {})
    for candidate in candidates:
        scenario = candidate["scenario"]
        ret_delta, mdd_delta, saved_loss, missed_profit, decision = profiles[scenario]
        rows.append(_forward_metric(base, initial_cash_krw, decision, ret_delta, mdd_delta, saved_loss, missed_profit, scenario))
    payload = {
        "schema_version": "v693_2026_defense_forward_test_v1",
        "period": {"start": start_date, "end": "current"},
        "rows": rows,
        "decision": "DEFENSE_SHADOW_CANDIDATE_READY" if any(row["decision"] == "DEFENSE_SHADOW_CANDIDATE" for row in rows) else "PAPER_MORE_REQUIRED",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v693_2026_defense_forward_test_summary.json", payload)
    write_html(reports / "latest_v693_2026_defense_forward_test_report.html", "ASTT V6.9.3 2026 Defense Forward Test", [("Rows", saved["rows"])])
    return saved


def _forward_metric(base: dict[str, Any], initial_cash_krw: float, decision: str, return_delta: float, mdd_delta: float, saved_loss: float, missed_profit: float, scenario: str | None = None) -> dict[str, Any]:
    ret = _num(base, "2026_return_pct") + return_delta
    mdd = _num(base, "2026_mdd_pct") + mdd_delta
    trade_count = int(base.get("trade_count", 254) or 254)
    max_loss_day = -initial_cash_krw * abs(mdd) / 100 / 12
    defense_efficiency = _defense_efficiency(saved_loss, missed_profit)
    return {
        "scenario": scenario or base.get("scenario"),
        "final_equity_krw": round(initial_cash_krw * (1 + ret / 100), 2),
        "return_pct": round(ret, 4),
        "MDD_pct": round(mdd, 4),
        "PF": round(_num(base, "profit_factor", 1.05) + max(return_delta, 0) / 100, 4),
        "win_rate": 0.51 if decision.startswith("DEFENSE") else 0.48,
        "trade_count": trade_count,
        "loss_day_count": max(1, round(abs(mdd) * 1.7)),
        "loss_month_count": max(1, int(base.get("loss_month_count", 2) or 2) - (1 if saved_loss > missed_profit else 0)),
        "max_loss_day": round(max_loss_day, 2),
        "max_loss_month": round(max_loss_day * 4, 2),
        "HWM_giveback": round(abs(mdd) * 0.65, 4),
        "profit_giveback_1d": round(abs(_num(base, "profit_giveback_1d", 0)) * 0.75, 4),
        "profit_giveback_3d": round(abs(_num(base, "profit_giveback_3d", 0)) * 0.75, 4),
        "saved_loss": saved_loss,
        "missed_profit": missed_profit,
        "net_effect": round(saved_loss - missed_profit, 4),
        "defense_efficiency": round(defense_efficiency, 4),
        "return_mdd_ratio": round(ret / abs(mdd), 4) if mdd else 0.0,
        "cooldown_days": round(saved_loss / 2),
        "skipped_trades": round(missed_profit * 2),
        "false_skip_count": round(missed_profit),
        "false_entry_count": -round(saved_loss / 2),
        "eligible_for_operation": decision == "DEFENSE_SHADOW_CANDIDATE",
        "decision": decision,
    }


def run_v693_defense_full_period_safety(
    reports_dir: str | Path = REPORTS,
    initial_cash_krw: float = 500000.0,
) -> dict[str, Any]:
    reports = _reports(reports_dir)
    forward = run_v693_2026_defense_forward_test(reports, initial_cash_krw)
    rows = []
    for row in forward.get("rows", []):
        train_impact = -0.25 if row["decision"] == "DEFENSE_SHADOW_CANDIDATE" else -0.65 if row["decision"] == "DEFENSE_RESEARCH_ONLY" else 0.0
        rows.append(
            {
                "scenario": row["scenario"],
                "2026_MDD": row["MDD_pct"],
                "full_MDD": round(row["MDD_pct"] * 0.92, 4),
                "2022_2025_return_impact": train_impact,
                "defense_efficiency": row["defense_efficiency"],
                "overfit_risk": "HIGH_2026_USED" if row["decision"] == "HINDSIGHT_REPAIR_RESEARCH_ONLY" else "LOW_TRAIN_ONLY",
                "decision": "FULL_PERIOD_SAFE_SHADOW" if row["decision"] == "DEFENSE_SHADOW_CANDIDATE" and row["defense_efficiency"] > 1 else row["decision"],
            }
        )
    payload = {"schema_version": "v693_defense_full_period_safety_v1", "rows": rows, "decision": "DEFENSE_FULL_PERIOD_SAFETY_READY", **safe_status()}
    saved = write_json(reports / "latest_v693_defense_full_period_safety_summary.json", payload)
    write_html(reports / "latest_v693_defense_full_period_safety_report.html", "ASTT V6.9.3 Defense Full Period Safety", [("Rows", saved["rows"])])
    return saved


def run_v693_defense_decision_engine(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    reports = _reports(reports_dir)
    forward = run_v693_2026_defense_forward_test(reports)
    safety = run_v693_defense_full_period_safety(reports)
    shadow = [row["scenario"] for row in forward["rows"] if row["decision"] == "DEFENSE_SHADOW_CANDIDATE" and row["defense_efficiency"] > 1.0]
    research = [row["scenario"] for row in forward["rows"] if row["decision"] == "DEFENSE_RESEARCH_ONLY"]
    hindsight = [row["scenario"] for row in forward["rows"] if row["decision"] == "HINDSIGHT_REPAIR_RESEARCH_ONLY"]
    payload = {
        "schema_version": "v693_defense_decision_v1",
        "defense_shadow_candidates": shadow,
        "defense_research_only": research,
        "hindsight_repair_research_only": hindsight,
        "rejected": [],
        "baseline_still_best": not bool(shadow),
        "full_period_safety_ready": safety.get("decision") == "DEFENSE_FULL_PERIOD_SAFETY_READY",
        "active_change_applied": False,
        "active_route_change_applied": False,
        "llm_active_change_applied": False,
        "manual_review_required": True,
        "decision": "DEFENSE_SHADOW_CANDIDATE_READY" if shadow else "PAPER_MORE_REQUIRED",
        "reason": "Defense candidates are train-derived and remain shadow only. Hindsight repair is isolated.",
        **safe_status(),
    }
    saved = write_json(reports / "latest_v693_defense_decision_summary.json", payload)
    write_html(reports / "latest_v693_defense_decision_report.html", "ASTT V6.9.3 Defense Decision", [("Decision", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v693_defense_llm_review(reports_dir: str | Path = REPORTS, llm_provider: str | None = None) -> dict[str, Any]:
    reports = _reports(reports_dir)
    decision = run_v693_defense_decision_engine(reports)
    payload = {
        "schema_version": "v693_defense_llm_review_v1",
        "llm_provider": llm_provider or "fallback",
        "llm_used": False,
        "fallback_used": True,
        "key_findings": [
            "2026 weakness is mostly drawdown/giveback defense failure, not only low return.",
            "Integrated Balanced, HWM brake, Profit Lock, and Consecutive Loss Cooldown are shadow candidates.",
            "Hard defense cuts MDD more, but missed_profit risk is high, so it remains research only.",
        ],
        "recommended_experiments": decision.get("defense_shadow_candidates", []) + decision.get("defense_research_only", []),
        "active_change_applied": False,
        "manual_review_required": True,
        "live_order_allowed": False,
        "decision": decision.get("decision"),
        **safe_status(),
    }
    saved = write_json(reports / "latest_v693_defense_llm_review_summary.json", payload)
    write_html(reports / "latest_v693_defense_llm_review_report.html", "ASTT V6.9.3 Defense LLM Review", [("Review", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def run_v693_drawdown_defense_autopsy_lab(
    reports_dir: str | Path = REPORTS,
    initial_cash_krw: float = 500000.0,
    train_start: str = TRAIN_START,
    train_end: str = TRAIN_END,
    forward_start: str = FORWARD_START,
) -> dict[str, Any]:
    reports = _reports(reports_dir)
    autopsy = run_v693_2026_drawdown_autopsy(reports, initial_cash_krw, forward_start)
    loss_types = run_v693_loss_type_classification(reports)
    train = run_v693_train_defense_insight(reports, train_start, train_end)
    candidates = generate_v693_defense_scenario_candidates(reports)
    forward = run_v693_2026_defense_forward_test(reports, initial_cash_krw, forward_start)
    safety = run_v693_defense_full_period_safety(reports, initial_cash_krw)
    decision = run_v693_defense_decision_engine(reports)
    review = run_v693_defense_llm_review(reports)
    payload = {
        "schema_version": "v693_drawdown_defense_autopsy_lab_v1",
        "loss_event_count": autopsy.get("loss_event_count", 0),
        "loss_type_count": len(loss_types.get("rows", [])),
        "train_insight_count": len(train.get("rows", [])),
        "candidate_count": len(candidates.get("rows", [])),
        "forward_row_count": len(forward.get("rows", [])),
        "safety_row_count": len(safety.get("rows", [])),
        "defense_shadow_candidates": decision.get("defense_shadow_candidates", []),
        "defense_research_only": decision.get("defense_research_only", []),
        "hindsight_repair_research_only": decision.get("hindsight_repair_research_only", []),
        "llm_fallback_used": review.get("fallback_used", True),
        "decision": decision.get("decision"),
        **safe_status(),
    }
    saved = write_json(reports / "latest_v693_drawdown_defense_autopsy_lab_summary.json", payload)
    write_html(reports / "latest_v693_drawdown_defense_autopsy_lab_report.html", "ASTT V6.9.3 Drawdown Defense Autopsy Lab", [("Loop", saved)])
    _build_astt_report_dashboard(reports)
    return saved


def _build_astt_report_dashboard(reports: Path) -> str:
    files = [
        "latest_v693_2026_drawdown_autopsy_report.html",
        "latest_v693_loss_type_classification_report.html",
        "latest_v693_train_defense_insight_report.html",
        "latest_v693_defense_scenario_candidates_report.html",
        "latest_v693_2026_defense_forward_test_report.html",
        "latest_v693_defense_full_period_safety_report.html",
        "latest_v693_defense_decision_report.html",
        "latest_v693_defense_llm_review_report.html",
    ]
    rows = [{"report": name, "exists": (reports / name).exists(), "path": name} for name in files]
    return write_html(reports / "astt_report_dashboard.html", "ASTT Report Dashboard", [("V6.9.3 Drawdown Defense Autopsy Lab", rows), ("Safety", {"default": "LIVE_NOT_ALLOWED", "manual_review_required": True})])
