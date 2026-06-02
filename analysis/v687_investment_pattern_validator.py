from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_runtime_schema import safety_flags


def run_v687_investment_pattern_validation(
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
    output_name: str = "latest_v687_investment_pattern_validation_summary.json",
) -> dict[str, Any]:
    assert_live_orders_disabled()
    reports = Path(reports_dir)
    data = Path(data_dir)
    backfill = _read_json(reports / "latest_v683_backfill_20260101_summary.json")
    trades = _read_jsonl(data / "journal" / "paper_trades.jsonl")
    latest_run_id = _latest_run_id(trades) or str(backfill.get("run_id") or "")
    trades = [row for row in trades if str(row.get("trade_id", "")).startswith(latest_run_id)]
    decisions = [row for row in _read_jsonl(data / "journal" / "paper_decisions.jsonl") if str(row.get("decision_id", "")).startswith(latest_run_id)]
    joined = _join_trades_decisions(trades, decisions)
    payload = {
        "schema_version": "v687_investment_pattern_validation_v1",
        "generated_at": datetime.utcnow().isoformat(),
        "source_backfill_run_id": backfill.get("run_id"),
        "journal_run_id_used": latest_run_id,
        "data_range": _data_range(joined),
        "surge_definition": "trade pnl_pct >= 0.50",
        "surge_patterns": _surge_patterns(joined),
        "risk_reward_patterns": _risk_reward_patterns(joined),
        "february_feedback": _february_feedback(backfill, joined),
        "drawdown_cut_sweep": _drawdown_cut_sweep(joined),
        "route_selection_policy": _route_selection_policy(backfill),
        "plain_language": _plain_language(),
        "decision": "PAPER_VALIDATOR_READY",
        **safety_flags(),
    }
    _write(reports / output_name, payload)
    return payload


def _join_trades_decisions(trades: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(row.get("decision_id")): row for row in decisions}
    rows = []
    for trade in trades:
        decision = by_id.get(str(trade.get("trade_id")), {})
        pnl = float(trade.get("realized_pnl_krw", trade.get("pnl_krw", 0.0)) or 0.0)
        pnl_pct = float(trade.get("pnl_pct", 0.0) or 0.0)
        size = float(trade.get("size_krw", 0.0) or 0.0)
        rows.append(
            {
                **trade,
                "time": trade.get("entry_time") or decision.get("decision_time"),
                "date": str(trade.get("entry_time") or decision.get("decision_time") or "")[:10],
                "month": str(trade.get("entry_time") or decision.get("decision_time") or "")[:7],
                "pnl_krw": pnl,
                "pnl_pct": pnl_pct,
                "size_krw": size,
                "market_state": decision.get("market_state"),
                "selected_agent": decision.get("selected_agent"),
                "action": decision.get("action"),
                "reason": decision.get("reason", []),
                "guard_on": decision.get("guard_on"),
                "hard_guard": decision.get("hard_guard"),
                "dominance_risk": decision.get("dominance_risk"),
                "pf20": _float_or_none(decision.get("pf20")),
                "month_return_pct": _float_or_none(decision.get("month_return_pct")),
                "hwm_drawdown_pct": _float_or_none(decision.get("hwm_drawdown_pct")),
            }
        )
    return sorted(rows, key=lambda row: str(row.get("time", "")))


def _latest_run_id(trades: list[dict[str, Any]]) -> str:
    run_ids = []
    for row in trades:
        trade_id = str(row.get("trade_id", ""))
        if ":" in trade_id:
            run_ids.append(trade_id.split(":", 1)[0])
    return max(run_ids, default="")


def _surge_patterns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("market_state") or "UNKNOWN"),
            "DOM_RISK" if row.get("dominance_risk") else "DOM_OK",
            _pf_bucket(row.get("pf20")),
            _month_bucket(row.get("month_return_pct")),
            _dd_bucket(row.get("hwm_drawdown_pct")),
            str(row.get("action") or "UNKNOWN"),
        )
        buckets[key].append(row)
    output = []
    for key, items in buckets.items():
        if len(items) < 5:
            continue
        surge = [row for row in items if float(row.get("pnl_pct", 0.0)) >= 0.50]
        summary = _trade_summary(items)
        output.append(
            {
                "pattern": " | ".join(key),
                "trade_count": len(items),
                "surge_count": len(surge),
                "surge_rate_pct": len(surge) / len(items) * 100.0,
                **summary,
                "interpretation": _pattern_interpretation(summary, len(surge) / len(items)),
            }
        )
    return sorted(output, key=lambda row: (row["surge_rate_pct"], row["profit_factor"], row["trade_count"]), reverse=True)[:30]


def _risk_reward_patterns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("market_state") or "UNKNOWN"),
            _pf_bucket(row.get("pf20")),
            _dd_bucket(row.get("hwm_drawdown_pct")),
            _reason_bucket(row.get("reason")),
        )
        buckets[key].append(row)
    output = []
    for key, items in buckets.items():
        if len(items) < 5:
            continue
        summary = _trade_summary(items)
        output.append({"pattern": " | ".join(key), "trade_count": len(items), **summary})
    return sorted(output, key=lambda row: (row["avg_win_loss_ratio"], row["profit_factor"], row["trade_count"]), reverse=True)[:30]


def _february_feedback(backfill: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    feb_rows = [row for row in rows if row.get("month") == "2026-02"]
    monthly = []
    for route_id, route_rows in backfill.get("monthly_returns", {}).items():
        row = next((item for item in route_rows if item.get("period") == "2026-02"), None)
        if row:
            monthly.append({"route_id": route_id, **row})
    monthly_sorted = sorted(monthly, key=lambda row: float(row.get("return_pct", -999.0)), reverse=True)
    losses = sorted([row for row in feb_rows if float(row.get("pnl_krw", 0.0)) < 0.0], key=lambda row: float(row.get("pnl_krw", 0.0)))[:15]
    by_state = _group_summary(feb_rows, "market_state")
    by_action = _group_summary(feb_rows, "action")
    active = next((row for row in monthly if row.get("route_id") == backfill.get("active_route")), {})
    best = monthly_sorted[0] if monthly_sorted else {}
    return {
        "active_route": backfill.get("active_route"),
        "active_february": active,
        "best_february_route": best,
        "route_monthly_rank": monthly_sorted,
        "trade_summary": _trade_summary(feb_rows),
        "by_market_state": by_state,
        "by_action": by_action,
        "largest_loss_trades": [
            {
                "time": row.get("time"),
                "market": row.get("market"),
                "pnl_krw": row.get("pnl_krw"),
                "pnl_pct": row.get("pnl_pct"),
                "market_state": row.get("market_state"),
                "action": row.get("action"),
                "pf20": row.get("pf20"),
                "hwm_drawdown_pct": row.get("hwm_drawdown_pct"),
                "reason": row.get("reason"),
            }
            for row in losses
        ],
        "insights": _february_insights(active, best, by_state, by_action),
    }


def _drawdown_cut_sweep(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for threshold in (-5.0, -8.0, -10.0, -12.0, -15.0):
        for mode, multiplier in (("skip", 0.0), ("reduce_35", 0.35)):
            adjusted = []
            for row in rows:
                dd = row.get("hwm_drawdown_pct")
                scale = multiplier if dd is not None and float(dd) <= threshold else 1.0
                adjusted.append({**row, "pnl_krw": float(row.get("pnl_krw", 0.0)) * scale, "pnl_pct": float(row.get("pnl_pct", 0.0)) * scale})
            summary = _trade_summary(adjusted)
            output.append({"threshold_hwm_drawdown_pct": threshold, "action_when_breached": mode, **summary})
    return sorted(output, key=lambda row: (row["max_drawdown_pct"], row["total_pnl_krw"]), reverse=True)


def _route_selection_policy(backfill: dict[str, Any]) -> dict[str, Any]:
    rows = backfill.get("active_vs_shadow_monthly", [])
    shadow_win_months = [row for row in rows if row.get("comment") == "shadow stronger"]
    return {
        "current_active_route": backfill.get("active_route"),
        "shadow_win_month_count": len(shadow_win_months),
        "monthly_shadow_winners": shadow_win_months,
        "paper_policy": [
            "월별 active 수익률이 음수이고 shadow가 active보다 2%p 이상 우위면 다음 paper 구간 candidate로 승격 표시",
            "shadow가 수익률은 높아도 MDD가 active보다 나쁘면 research-only",
            "자동 실거래 전환은 금지, 대시보드 표시는 paper route recommendation만 허용",
        ],
    }


def _trade_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "total_pnl_krw": 0.0,
            "return_pct_sum": 0.0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "avg_win_krw": 0.0,
            "avg_loss_krw": 0.0,
            "avg_win_loss_ratio": 0.0,
            "expectancy_krw": 0.0,
            "max_drawdown_pct": 0.0,
        }
    pnls = [float(row.get("pnl_krw", 0.0)) for row in rows]
    wins = [pnl for pnl in pnls if pnl > 0.0]
    losses = [pnl for pnl in pnls if pnl < 0.0]
    equity = 500000.0
    peak = equity
    mdd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        mdd = min(mdd, (equity / peak - 1.0) * 100.0 if peak else 0.0)
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    avg_win = mean(wins) if wins else 0.0
    avg_loss = abs(mean(losses)) if losses else 0.0
    return {
        "total_pnl_krw": sum(pnls),
        "return_pct_sum": sum(float(row.get("pnl_pct", 0.0)) for row in rows),
        "win_rate_pct": len(wins) / len(rows) * 100.0,
        "profit_factor": gross_win / gross_loss if gross_loss else 99.0 if gross_win else 0.0,
        "avg_win_krw": avg_win,
        "avg_loss_krw": avg_loss,
        "avg_win_loss_ratio": avg_win / avg_loss if avg_loss else 99.0 if avg_win else 0.0,
        "expectancy_krw": mean(pnls),
        "max_drawdown_pct": mdd,
    }


def _group_summary(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key) or "UNKNOWN")].append(row)
    output = []
    for value, items in groups.items():
        output.append({key: value, "trade_count": len(items), **_trade_summary(items)})
    return sorted(output, key=lambda row: row["total_pnl_krw"])


def _pf_bucket(value: Any) -> str:
    if value is None:
        return "PF_UNKNOWN"
    value = float(value)
    if value < 0.8:
        return "PF<0.8"
    if value < 1.0:
        return "PF0.8-1.0"
    if value < 1.2:
        return "PF1.0-1.2"
    return "PF>=1.2"


def _month_bucket(value: Any) -> str:
    if value is None:
        return "MONTH_UNKNOWN"
    value = float(value)
    if value < -5.0:
        return "MONTH<-5"
    if value < 0.0:
        return "MONTH<0"
    if value < 5.0:
        return "MONTH0-5"
    return "MONTH>=5"


def _dd_bucket(value: Any) -> str:
    if value is None:
        return "DD_UNKNOWN"
    value = float(value)
    if value <= -15.0:
        return "DD<=-15"
    if value <= -10.0:
        return "DD-10~-15"
    if value <= -5.0:
        return "DD-5~-10"
    return "DD>-5"


def _reason_bucket(value: Any) -> str:
    reasons = value if isinstance(value, list) else []
    if any("LOSS_GUARD" in str(item) for item in reasons):
        return "LOSS_GUARD"
    if any("ROLLING" in str(item) for item in reasons):
        return "ROLLING"
    if any("PLAN_A" in str(item) for item in reasons):
        return "PLAN_A"
    return "OTHER"


def _pattern_interpretation(summary: dict[str, Any], surge_rate: float) -> str:
    if surge_rate >= 0.35 and summary["profit_factor"] >= 1.2:
        return "급등 후보로 paper 우선관찰"
    if summary["profit_factor"] < 1.0 or summary["avg_win_loss_ratio"] < 1.0:
        return "손익비 열위, 진입 축소 후보"
    return "중립"


def _february_insights(active: dict[str, Any], best: dict[str, Any], by_state: list[dict[str, Any]], by_action: list[dict[str, Any]]) -> list[str]:
    insights = []
    if active:
        insights.append(f"2월 active return={float(active.get('return_pct', 0.0)):.2f}%, MDD={float(active.get('mdd_pct', 0.0)):.2f}%.")
    if best and best.get("route_id") != active.get("route_id"):
        insights.append(f"2월 최상위 route는 {best.get('route_id')}로 active보다 {float(best.get('return_pct', 0.0)) - float(active.get('return_pct', 0.0)):.2f}%p 우위.")
    worst_state = by_state[0] if by_state else {}
    if worst_state:
        insights.append(f"손실이 큰 시장상태는 {worst_state.get('market_state')}이며 총손익 {float(worst_state.get('total_pnl_krw', 0.0)):.0f} KRW.")
    worst_action = by_action[0] if by_action else {}
    if worst_action:
        insights.append(f"손실이 큰 action은 {worst_action.get('action')}이며 거래수 {worst_action.get('trade_count')}.")
    insights.append("개선안: 2월 같은 고점대비 낙폭 확대 구간에서는 PF20<0.8 또는 DD<=-10%일 때 skip/reduce_35 paper rule을 우선 비교.")
    return insights


def _plain_language() -> dict[str, str]:
    return {
        "drawdown_formula": "현재 평가금이 직전 최고 평가금보다 얼마나 내려왔는지 보는 값입니다. drawdown_pct = (현재평가금 / 최고평가금 - 1) * 100, MDD는 그중 가장 낮은 값입니다.",
        "cutting_drawdown": "낙폭을 끊는 손절/축소는 필요합니다. 단, 너무 빠른 손절은 회복 거래와 급등 거래까지 잘라 수익률을 죽일 수 있어 threshold sweep으로 검증해야 합니다.",
        "risk_reward": "여기서 손익비는 평균 이익금 / 평균 손실금입니다. PF는 총이익 / 총손실이라 둘을 같이 봐야 합니다.",
    }


def _data_range(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dates = [str(row.get("date")) for row in rows if row.get("date")]
    return {"start": min(dates, default=None), "end": max(dates, default=None), "trade_count": len(rows)}


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(run_v687_investment_pattern_validation(), ensure_ascii=False, default=str))
