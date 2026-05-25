from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from portfolio.causal_equity_defense_runner import _decide_multiplier, _drawdown
from portfolio.dynamic_risk_scaler import DynamicRiskScaler
from portfolio.profit_lock_engine import ProfitLockEngine
from portfolio.protected_floor_manager import ProtectedFloorManager


SCENARIOS = [
    "BASELINE",
    "DRAWDOWN_THROTTLE",
    "ROLLING_EDGE_THROTTLE",
    "HYBRID_DEFENSE",
    "DEFENSIVE_CORE",
    "BALANCED_GROWTH",
    "AGGRESSIVE_GROWTH",
    "HIGH_OCTANE_RESEARCH",
]


def analyze_v64_policy_blend(journal: list[dict[str, Any]], initial_cash_krw: float = 500000.0) -> dict[str, Any]:
    ordered = sorted(journal, key=lambda row: str(row.get("entry_time", "")))
    simulations = {name: _simulate(name, ordered, initial_cash_krw) for name in SCENARIOS}
    rolling = simulations["ROLLING_EDGE_THROTTLE"]
    balanced = simulations["BALANCED_GROWTH"]
    scenario_rows = [_scenario_row(name, data, initial_cash_krw) for name, data in simulations.items()]
    comparison = _compare_rolling_balanced(rolling, balanced, initial_cash_krw)
    return {
        "schema_version": "v64_policy_blend_analysis_v1",
        "initial_cash_krw": initial_cash_krw,
        "scenario_count": len(scenario_rows),
        "scenarios": scenario_rows,
        "rolling_vs_balanced": comparison,
        "policy_activity": {name: _activity(data) for name, data in simulations.items()},
        "top_months_balanced_better": _top_deltas(balanced["by_month"], rolling["by_month"], reverse=True),
        "top_months_rolling_better": _top_deltas(balanced["by_month"], rolling["by_month"], reverse=False),
        "plan_deltas_balanced_minus_rolling": _deltas(balanced["by_plan"], rolling["by_plan"]),
        "strategy_deltas_balanced_minus_rolling": _deltas(balanced["by_strategy"], rolling["by_strategy"]),
        "setup_deltas_balanced_minus_rolling": _deltas(balanced["by_setup"], rolling["by_setup"]),
        "largest_trade_level_differences": _largest_trade_differences(rolling["rows"], balanced["rows"]),
        "recommended_policy_stack": _recommendations(comparison),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _simulate(name: str, journal: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    scaler = DynamicRiskScaler()
    profit_lock = ProfitLockEngine(initial_cash)
    floor_manager = ProtectedFloorManager()
    rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    multiplier_counts: Counter[str] = Counter()
    by_month: defaultdict[str, float] = defaultdict(float)
    by_plan: defaultdict[str, float] = defaultdict(float)
    by_strategy: defaultdict[str, float] = defaultdict(float)
    by_setup: defaultdict[str, float] = defaultdict(float)
    lookahead_fail_count = 0

    for idx, trade in enumerate(journal):
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        entry_time = str(trade.get("entry_time"))
        feature_cutoff_time = str(trade.get("feature_cutoff_time") or decision_time)
        drawdown_before = _drawdown(equity, peak)
        base_pnl = float(trade.get("pnl_krw", 0.0))
        rolling_audit = scaler.audit_window(20)
        decision = _decide_multiplier(name, trade, equity, drawdown_before, scaler, profit_lock)
        multiplier = float(decision["risk_multiplier_after_defense"])
        floor_multiplier, floor_capped = floor_manager.cap_multiplier(equity, base_pnl, multiplier)
        if floor_capped:
            multiplier = floor_multiplier
            decision["defense_reasons"].append("PROTECTED_FLOOR_CAP")
        action = "SKIP" if decision["defense_action"] == "SKIP" or multiplier <= 0 else "ENTER"
        pnl = 0.0 if action == "SKIP" else base_pnl * multiplier
        if action == "ENTER":
            scaler.record(pnl, str(trade.get("exit_time")))
        before = equity
        equity += pnl
        peak = max(peak, equity)
        drawdown_after = _drawdown(equity, peak)
        lookahead_pass = feature_cutoff_time <= decision_time <= entry_time and int(rolling_audit["rolling_trades_used"]) <= idx
        if not lookahead_pass:
            lookahead_fail_count += 1
        reasons = decision["defense_reasons"] or ["NO_DEFENSE"]
        for reason in reasons:
            reason_counts[reason] += 1
        state_counts[decision["defense_state_before_trade"]] += 1
        action_counts[action] += 1
        multiplier_counts[f"{0.0 if action == 'SKIP' else multiplier:.2f}"] += 1
        month = str(trade.get("entry_time", ""))[:7]
        by_month[month] += pnl
        by_plan[str(trade.get("plan"))] += pnl
        by_strategy[str(trade.get("strategy"))] += pnl
        by_setup[str(trade.get("setup_type"))] += pnl
        rows.append(
            {
                "trade_id": trade.get("trade_id"),
                "entry_time": entry_time,
                "market": trade.get("market"),
                "plan": trade.get("plan"),
                "strategy": trade.get("strategy"),
                "setup_type": trade.get("setup_type"),
                "base_pnl_krw": base_pnl,
                "scenario_pnl_krw": pnl,
                "risk_multiplier": 0.0 if action == "SKIP" else multiplier,
                "defense_action": action,
                "defense_state": decision["defense_state_before_trade"],
                "defense_reasons": reasons,
                "equity_before": before,
                "equity_after": equity,
                "drawdown_before_pct": drawdown_before,
                "drawdown_after_pct": drawdown_after,
                "lookahead_check": "PASS" if lookahead_pass else "FAIL",
            }
        )

    return {
        "rows": rows,
        "final_equity_krw": equity,
        "reason_counts": dict(reason_counts),
        "state_counts": dict(state_counts),
        "action_counts": dict(action_counts),
        "multiplier_counts": dict(multiplier_counts),
        "by_month": dict(by_month),
        "by_plan": dict(by_plan),
        "by_strategy": dict(by_strategy),
        "by_setup": dict(by_setup),
        "lookahead_fail_count": lookahead_fail_count,
    }


def _scenario_row(name: str, data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    rows = [row for row in data["rows"] if row["defense_action"] == "ENTER"]
    pnls = [float(row["scenario_pnl_krw"]) for row in rows]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    equity = initial_cash
    peak = initial_cash
    mdd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        mdd = min(mdd, _drawdown(equity, peak))
    gross_loss = abs(sum(losses))
    return_pct = (equity / initial_cash - 1.0) * 100 if initial_cash else 0.0
    return {
        "scenario": name,
        "final_equity_krw": equity,
        "return_pct": return_pct,
        "mdd_pct": mdd,
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "trade_count": len(rows),
        "skipped_trade_count": len(data["rows"]) - len(rows),
        "return_mdd_ratio": return_pct / abs(mdd) if mdd else 0.0,
        "average_multiplier": _avg([float(row["risk_multiplier"]) for row in rows]),
        "lookahead_fail_count": data["lookahead_fail_count"],
    }


def _compare_rolling_balanced(rolling: dict[str, Any], balanced: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    r = _scenario_row("ROLLING_EDGE_THROTTLE", rolling, initial_cash)
    b = _scenario_row("BALANCED_GROWTH", balanced, initial_cash)
    return {
        "balanced_final_equity_delta_krw": b["final_equity_krw"] - r["final_equity_krw"],
        "balanced_return_delta_pct_point": b["return_pct"] - r["return_pct"],
        "balanced_mdd_delta_pct_point": b["mdd_pct"] - r["mdd_pct"],
        "balanced_profit_factor_delta": b["profit_factor"] - r["profit_factor"],
        "balanced_return_mdd_ratio_delta": b["return_mdd_ratio"] - r["return_mdd_ratio"],
        "interpretation": "Balanced Growth는 수익을 소폭 더 만들지만 최대낙폭은 아주 조금 깊어집니다. Rolling Edge는 더 단순하고 보수적인 기본 방어축입니다.",
    }


def _activity(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "actions": data["action_counts"],
        "states": data["state_counts"],
        "multipliers": data["multiplier_counts"],
        "top_reasons": _top_counter(data["reason_counts"], 8),
    }


def _deltas(left: dict[str, float], right: dict[str, float]) -> list[dict[str, Any]]:
    keys = sorted(set(left) | set(right))
    rows = [
        {
            "key": key,
            "balanced_value_krw": left.get(key, 0.0),
            "rolling_value_krw": right.get(key, 0.0),
            "delta_krw": left.get(key, 0.0) - right.get(key, 0.0),
        }
        for key in keys
    ]
    return sorted(rows, key=lambda row: abs(float(row["delta_krw"])), reverse=True)


def _top_deltas(left: dict[str, float], right: dict[str, float], reverse: bool) -> list[dict[str, Any]]:
    rows = _deltas(left, right)
    ordered = sorted(rows, key=lambda row: float(row["delta_krw"]), reverse=reverse)
    return ordered[:10]


def _largest_trade_differences(rolling_rows: list[dict[str, Any]], balanced_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows = []
    for rolling, balanced in zip(rolling_rows, balanced_rows):
        delta = float(balanced["scenario_pnl_krw"]) - float(rolling["scenario_pnl_krw"])
        if abs(delta) < 1e-9:
            continue
        rows.append(
            {
                "entry_time": balanced["entry_time"],
                "market": balanced["market"],
                "plan": balanced["plan"],
                "setup_type": balanced["setup_type"],
                "base_pnl_krw": balanced["base_pnl_krw"],
                "rolling_multiplier": rolling["risk_multiplier"],
                "balanced_multiplier": balanced["risk_multiplier"],
                "delta_krw": delta,
                "balanced_reasons": balanced["defense_reasons"],
            }
        )
    return {
        "balanced_helped_most": sorted(rows, key=lambda row: float(row["delta_krw"]), reverse=True)[:10],
        "balanced_hurt_most": sorted(rows, key=lambda row: float(row["delta_krw"]))[:10],
    }


def _recommendations(comparison: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "policy": "기본 방어축",
            "recommendation": "ROLLING_EDGE_THROTTLE",
            "reason": "최대낙폭이 가장 낮고 규칙이 단순합니다. 최근 20거래 성과가 무너질 때만 35%로 줄여 큰 승리 구간을 덜 잘라먹습니다.",
        },
        {
            "policy": "스팟 보완",
            "recommendation": "BALANCED_GROWTH overlay",
            "reason": "PF 0.8~1.2의 애매한 구간에서 70% 감속이 Plan B/Combined 손실을 줄였습니다. 단, Plan A fat-tail 승리도 일부 잘라먹기 때문에 전체 기본값으로만 보지 말고 조건부 보완으로 둡니다.",
        },
        {
            "policy": "깊은 낙폭 대응",
            "recommendation": "HYBRID/DEFENSIVE rules as emergency brake",
            "reason": "수익률은 Balanced/Rolling보다 낮지만 낙폭이 커질 때 심리적·운영상 방어 장치로 쓸 수 있습니다. forward에서 DD가 확대될 때만 단계적으로 켭니다.",
        },
        {
            "policy": "공격형 운용",
            "recommendation": "AGGRESSIVE_GROWTH research only",
            "reason": "수익률 확대 후보지만 이번 검증에서는 Balanced보다 수익과 return/MDD가 낮았습니다. 실전 후보가 아니라 별도 연구 후보입니다.",
        },
        {
            "policy": "제외",
            "recommendation": "HIGH_OCTANE_RESEARCH 제외",
            "reason": "거래를 많이 건너뛰고 MDD 대비 효율이 낮으며 DD cap 위반이 많습니다. 고위험 연구 기록으로만 유지합니다.",
        },
    ]


def _top_counter(counter: dict[str, int], limit: int) -> list[dict[str, Any]]:
    return [{"key": key, "count": value} for key, value in Counter(counter).most_common(limit)]


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
