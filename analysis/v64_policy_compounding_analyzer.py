from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from portfolio.causal_equity_defense_runner import _decide_multiplier, _drawdown
from portfolio.dynamic_risk_scaler import DynamicRiskScaler
from portfolio.profit_lock_engine import ProfitLockEngine
from portfolio.protected_floor_manager import ProtectedFloorManager
from risk.risk_position_sizer import size_position


POLICIES = ["ROLLING_EDGE_THROTTLE", "BALANCED_GROWTH"]


def analyze_policy_aware_compounding(
    journal: list[dict[str, Any]],
    initial_cash_krw: float = 500000.0,
) -> dict[str, Any]:
    ordered = sorted(journal, key=lambda row: str(row.get("entry_time", "")))
    scenarios = {policy: _simulate_policy(policy, ordered, initial_cash_krw) for policy in POLICIES}
    rolling = scenarios["ROLLING_EDGE_THROTTLE"]
    balanced = scenarios["BALANCED_GROWTH"]
    return {
        "schema_version": "v64_policy_aware_compounding_v1",
        "description": "Rolling Edge와 Balanced Growth를 각각 독립 계좌로 두고 매 거래마다 해당 정책의 현재 평가금 기준으로 포지션을 재산정한 복리 검증입니다.",
        "initial_cash_krw": initial_cash_krw,
        "scenarios": [_scenario_summary(name, data, initial_cash_krw) for name, data in scenarios.items()],
        "rolling_vs_balanced": _compare(rolling, balanced, initial_cash_krw),
        "period_returns": {
            name: {
                "weekly": _period_rows(data["journal"], "week"),
                "monthly": _period_rows(data["journal"], "month"),
                "yearly": _period_rows(data["journal"], "year"),
            }
            for name, data in scenarios.items()
        },
        "plan_performance": {name: _group_performance(data["journal"], "plan") for name, data in scenarios.items()},
        "strategy_performance": {name: _group_performance(data["journal"], "strategy") for name, data in scenarios.items()},
        "policy_activity": {name: _activity(data) for name, data in scenarios.items()},
        "equity_curve": {name: _sample_curve(data["equity_curve"]) for name, data in scenarios.items()},
        "drawdown_curve": {name: _sample_curve(data["drawdown_curve"]) for name, data in scenarios.items()},
        "recommendation": _recommendation(rolling, balanced, initial_cash_krw),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _simulate_policy(policy: str, source_journal: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    equity = initial_cash
    peak = initial_cash
    scaler = DynamicRiskScaler()
    profit_lock = ProfitLockEngine(initial_cash)
    floor_manager = ProtectedFloorManager()
    journal: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    drawdown_curve: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    multiplier_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()

    for idx, trade in enumerate(source_journal):
        decision_time = str(trade.get("feature_cutoff_time") or trade.get("signal_time") or trade.get("entry_time"))
        entry_time = str(trade.get("entry_time"))
        feature_cutoff_time = str(trade.get("feature_cutoff_time") or decision_time)
        drawdown_before = _drawdown(equity, peak)
        rolling_audit = scaler.audit_window(20)
        decision = _decide_multiplier(policy, trade, equity, drawdown_before, scaler, profit_lock)
        multiplier = float(decision["risk_multiplier_after_defense"])
        action = "SKIP" if decision["defense_action"] == "SKIP" or multiplier <= 0 else "ENTER"
        sizing = size_position(equity, float(trade.get("entry_price", 0.0)), float(trade.get("stop_price", 0.0)))
        if not sizing.get("sizing_valid"):
            action = "SKIP"
            decision["defense_reasons"].append(str(sizing.get("reason") or "INVALID_SIZING"))

        position_krw = 0.0
        pnl = 0.0
        if action == "ENTER":
            base_position = min(float(sizing["position_krw"]), equity)
            floor_multiplier, floor_capped = floor_manager.cap_multiplier(equity, _unit_pnl(trade, base_position), multiplier)
            if floor_capped:
                multiplier = floor_multiplier
                decision["defense_reasons"].append("PROTECTED_FLOOR_CAP")
            position_krw = base_position * multiplier
            pnl = _unit_pnl(trade, position_krw)
            scaler.record(pnl, str(trade.get("exit_time")))

        equity_before = equity
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        drawdown_after = _drawdown(equity, peak)
        lookahead_pass = feature_cutoff_time <= decision_time <= entry_time and int(rolling_audit["rolling_trades_used"]) <= idx
        reasons = decision["defense_reasons"] or ["NO_DEFENSE"]
        for reason in reasons:
            reason_counts[reason] += 1
        state_counts[decision["defense_state_before_trade"]] += 1
        action_counts[action] += 1
        multiplier_counts[f"{0.0 if action == 'SKIP' else multiplier:.2f}"] += 1
        row = {
            "trade_id": trade.get("trade_id"),
            "date": str(trade.get("entry_time", ""))[:10],
            "entry_time": entry_time,
            "exit_time": trade.get("exit_time"),
            "market": trade.get("market"),
            "plan": trade.get("plan"),
            "strategy": trade.get("strategy"),
            "setup_type": trade.get("setup_type"),
            "entry_price": float(trade.get("entry_price", 0.0)),
            "exit_price": float(trade.get("exit_price", 0.0)),
            "stop_price": float(trade.get("stop_price", 0.0)),
            "target_price": float(trade.get("target_price", 0.0)),
            "risk_amount_krw": float(sizing.get("risk_amount_krw", 0.0)) * (0.0 if action == "SKIP" else multiplier),
            "position_krw": position_krw,
            "pnl_krw": pnl,
            "return_pct": pnl / equity_before * 100 if equity_before else 0.0,
            "equity_before": equity_before,
            "equity_after": equity,
            "drawdown_pct": drawdown_after,
            "policy": policy,
            "defense_state_before_trade": decision["defense_state_before_trade"],
            "risk_multiplier_after_defense": 0.0 if action == "SKIP" else multiplier,
            "defense_action": action,
            "defense_reasons": reasons,
            "feature_cutoff_time": feature_cutoff_time,
            "decision_time": decision_time,
            "used_future_data": False,
            "lookahead_check": "PASS" if lookahead_pass else "FAIL",
            "real_order_enabled": False,
            "live_order_allowed": False,
            "auto_apply_allowed": False,
        }
        journal.append(row)
        equity_curve.append({"sequence": idx, "time": trade.get("exit_time"), "equity": equity})
        drawdown_curve.append({"sequence": idx, "time": trade.get("exit_time"), "drawdown_pct": drawdown_after})

    return {
        "journal": journal,
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "reason_counts": dict(reason_counts),
        "state_counts": dict(state_counts),
        "multiplier_counts": dict(multiplier_counts),
        "action_counts": dict(action_counts),
    }


def _unit_pnl(trade: dict[str, Any], position_krw: float) -> float:
    entry = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", 0.0))
    if entry <= 0:
        return 0.0
    return position_krw * ((exit_price / entry) - 1.0) - position_krw * 0.001


def _scenario_summary(policy: str, data: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    entered = [row for row in data["journal"] if row["defense_action"] == "ENTER"]
    pnls = [float(row["pnl_krw"]) for row in entered]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    final_equity = float(data["journal"][-1]["equity_after"]) if data["journal"] else initial_cash
    mdd = min((float(row["drawdown_pct"]) for row in data["journal"]), default=0.0)
    gross_loss = abs(sum(losses))
    ret = (final_equity / initial_cash - 1.0) * 100 if initial_cash else 0.0
    return {
        "scenario": policy,
        "initial_cash_krw": initial_cash,
        "final_equity_krw": final_equity,
        "return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": sum(wins) / gross_loss if gross_loss else 99.0 if wins else 0.0,
        "expectancy_pct": ((sum(pnls) / len(pnls)) / initial_cash * 100) if pnls else 0.0,
        "trade_count": len(entered),
        "skipped_trade_count": len(data["journal"]) - len(entered),
        "win_rate_pct": len(wins) / len(pnls) * 100 if pnls else 0.0,
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "average_position_krw": _avg([float(row["position_krw"]) for row in entered]),
        "average_multiplier": _avg([float(row["risk_multiplier_after_defense"]) for row in entered]),
        "lookahead_fail_count": sum(1 for row in data["journal"] if row["lookahead_check"] != "PASS"),
    }


def _compare(rolling: dict[str, Any], balanced: dict[str, Any], initial_cash: float) -> dict[str, Any]:
    r = _scenario_summary("ROLLING_EDGE_THROTTLE", rolling, initial_cash)
    b = _scenario_summary("BALANCED_GROWTH", balanced, initial_cash)
    return {
        "balanced_final_equity_delta_krw": b["final_equity_krw"] - r["final_equity_krw"],
        "balanced_return_delta_pct_point": b["return_pct"] - r["return_pct"],
        "balanced_mdd_delta_pct_point": b["mdd_pct"] - r["mdd_pct"],
        "balanced_profit_factor_delta": b["profit_factor"] - r["profit_factor"],
        "balanced_return_mdd_ratio_delta": b["return_mdd_ratio"] - r["return_mdd_ratio"],
    }


def _period_rows(journal: list[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        key = _period_key(str(row.get("date")), period)
        groups[key].append(row)
    rows = []
    for key, items in sorted(groups.items()):
        entered = [row for row in items if row["defense_action"] == "ENTER"]
        wins = [row for row in entered if float(row.get("pnl_krw", 0.0)) > 0]
        losses = [row for row in entered if float(row.get("pnl_krw", 0.0)) < 0]
        start = float(items[0]["equity_before"])
        end = float(items[-1]["equity_after"])
        gross_win = sum(float(row.get("pnl_krw", 0.0)) for row in wins)
        gross_loss = abs(sum(float(row.get("pnl_krw", 0.0)) for row in losses))
        rows.append(
            {
                "period": key,
                "start_equity": start,
                "end_equity": end,
                "return_pct": (end - start) / start * 100 if start else 0.0,
                "trades": len(entered),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate_pct": len(wins) / len(entered) * 100 if entered else 0.0,
                "profit_factor": gross_win / gross_loss if gross_loss else 99.0 if wins else 0.0,
                "mdd_pct": min(float(row.get("drawdown_pct", 0.0)) for row in items),
                "main_strategy": Counter(str(row.get("strategy")) for row in entered).most_common(1)[0][0] if entered else "NO_TRADE",
            }
        )
    return rows


def _period_key(date_text: str, period: str) -> str:
    from datetime import datetime

    dt = datetime.fromisoformat(date_text[:10])
    if period == "year":
        return str(dt.year)
    if period == "month":
        return f"{dt.year:04d}-{dt.month:02d}"
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year:04d}-W{iso_week:02d}"


def _group_performance(journal: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        if row["defense_action"] == "ENTER":
            groups[str(row.get(key))].append(row)
    rows = []
    for name, items in sorted(groups.items()):
        pnl = sum(float(row.get("pnl_krw", 0.0)) for row in items)
        wins = [row for row in items if float(row.get("pnl_krw", 0.0)) > 0]
        losses = [row for row in items if float(row.get("pnl_krw", 0.0)) < 0]
        gross_win = sum(float(row.get("pnl_krw", 0.0)) for row in wins)
        gross_loss = abs(sum(float(row.get("pnl_krw", 0.0)) for row in losses))
        rows.append(
            {
                key: name,
                "trade_count": len(items),
                "pnl_krw": pnl,
                "win_rate_pct": len(wins) / len(items) * 100 if items else 0.0,
                "profit_factor": gross_win / gross_loss if gross_loss else 99.0 if wins else 0.0,
            }
        )
    return rows


def _activity(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "actions": data["action_counts"],
        "states": data["state_counts"],
        "multipliers": data["multiplier_counts"],
        "top_reasons": Counter(data["reason_counts"]).most_common(8),
    }


def _recommendation(rolling: dict[str, Any], balanced: dict[str, Any], initial_cash: float) -> dict[str, str]:
    r = _scenario_summary("ROLLING_EDGE_THROTTLE", rolling, initial_cash)
    b = _scenario_summary("BALANCED_GROWTH", balanced, initial_cash)
    if b["return_mdd_ratio"] > r["return_mdd_ratio"] and b["mdd_pct"] > r["mdd_pct"] - 1.0:
        return {
            "primary": "BALANCED_GROWTH",
            "secondary": "ROLLING_EDGE_THROTTLE",
            "reason": "정책별 독립 복리 재검증에서도 Balanced의 Return/MDD 효율이 더 높고, Rolling 대비 낙폭 추가 부담이 제한적입니다.",
        }
    return {
        "primary": "ROLLING_EDGE_THROTTLE",
        "secondary": "BALANCED_GROWTH_OVERLAY",
        "reason": "정책별 독립 복리 재검증에서 Rolling의 낙폭 방어가 더 우수하므로 기본 방어축으로 두고 Balanced는 조건부 보완으로 둡니다.",
    }


def _sample_curve(rows: list[dict[str, Any]], target: int = 240) -> list[dict[str, Any]]:
    if len(rows) <= target:
        return rows
    step = max(1, len(rows) // target)
    sample = rows[::step]
    return sample + ([rows[-1]] if sample[-1] != rows[-1] else [])


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
