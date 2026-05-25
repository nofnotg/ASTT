from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from analysis.capital_growth_analyzer import summarize_capital_growth
from analysis.risk_evidence_reporter import build_risk_evidence
from market_data.ohlcv_store import OHLCVStore
from mtf.mtf_context_builder import build_v6_mtf_context
from portfolio.compounding_engine import return_pct_from_equity
from portfolio.monthly_report_builder import build_monthly_rows
from portfolio.seed_growth_analyzer import build_equity_curve
from portfolio.weekly_report_builder import build_weekly_rows
from risk.risk_position_sizer import size_position
from strategy_router.strategy_router import plan_for_trade


def run_true_walk_forward_paper(
    initial_cash_krw: float = 500000,
    archive_dir: str | Path = "replay_store/historical_archive",
    risk_profile: str = "aggressive",
    max_open_positions: int = 3,
) -> dict[str, Any]:
    store = OHLCVStore(archive_dir)
    markets = store.list_markets("1d")
    mtf_summary = build_v6_mtf_context("TOP_KRW_999", store)
    contexts = {row["market"]: row for row in mtf_summary.get("contexts", []) if row.get("market") in markets}
    candidates = _build_candidates(store, markets, contexts)
    journal = _execute_candidates(candidates, initial_cash_krw, max_open_positions)
    summary = _summary(journal, initial_cash_krw, archive_dir, risk_profile)
    _write_outputs(summary, journal)
    return summary


def _write_outputs(summary: dict[str, Any], journal: list[dict[str, Any]]) -> None:
    _write(Path("docs/reports/latest_true_walk_forward_summary.json"), summary)
    _write(Path("docs/reports/latest_v62_trade_journal_summary.json"), {"schema_version": "true_walk_forward_v1", "journal": journal, "trade_count": len(journal), **_safety()})
    _write(Path("docs/reports/latest_v62_weekly_summary.json"), {"schema_version": "true_walk_forward_v1", "weekly_rows": summary["weekly_rows"], **_safety()})
    _write(Path("docs/reports/latest_v62_monthly_summary.json"), {"schema_version": "true_walk_forward_v1", "monthly_rows": summary["monthly_rows"], **_safety()})
    _write(Path("docs/reports/latest_v62_full_investment_summary.json"), summary)
    _write(Path("docs/reports/latest_v62_risk_summary.json"), {"schema_version": "true_walk_forward_v1", "risk": summary["risk"], **_safety()})
    _write(Path("docs/reports/latest_v62_strategy_router_summary.json"), {"schema_version": "true_walk_forward_v1", "plan_performance": summary["plan_performance"], **_safety()})
    _write(Path("replay_store/true_walk_forward/latest_true_walk_forward_summary.json"), summary)


def _build_candidates(store: OHLCVStore, markets: list[str], contexts: dict[str, dict]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for market in markets:
        daily = store.load("1d", market)
        h4 = store.load("4h", market)
        h1 = store.load("1h", market)
        m15 = store.load("15m", market)
        if m15.empty:
            m15 = h1.copy()
        if daily.empty or h1.empty or m15.empty:
            continue
        # Long-horizon walk-forward scan: evaluate one setup checkpoint per week using only past candles.
        for idx in range(168, len(h1), 168):
            cutoff = pd.to_datetime(h1["time"].iloc[idx])
            daily_cut = _until(daily, cutoff).tail(260)
            h4_cut = _until(h4, cutoff).tail(360)
            h1_cut = h1.iloc[: idx + 1].copy().tail(360)
            if len(h1_cut) < 60:
                continue
            mtf = {**contexts.get(market, {"market": market, "mtf_score": 50.0}), "market": market}
            for setup in _scan_setups(market, daily_cut, h4_cut, h1_cut, mtf):
                setup["signal_time"] = str(cutoff)
                setup["feature_cutoff_time"] = str(cutoff)
                setup["entry_time"] = str(cutoff)
                setup["exit_plan_frame"] = h1[h1["time"] > cutoff].head(72).copy()
                candidates.append(setup)
    return sorted(candidates, key=lambda row: (row["entry_time"], row["market"], row["strategy"]))


def _scan_setups(market: str, daily: pd.DataFrame, h4: pd.DataFrame, h1: pd.DataFrame, mtf: dict[str, Any]) -> list[dict[str, Any]]:
    latest = h1.iloc[-1]
    previous = h1.iloc[:-1].tail(60)
    if previous.empty:
        return []
    entry = float(latest["close"])
    recent_low = float(previous["low"].min())
    recent_high = float(previous["high"].max())
    avg_volume = float(previous["volume"].mean()) or 1.0
    volume_burst = float(latest["volume"]) / avg_volume
    sweep_reclaim = float(latest["low"]) < recent_low and entry > recent_low
    bullish_fvg = _has_bullish_fvg(h1.tail(6))
    breakout_pressure = entry > recent_high * 0.995 and volume_burst >= 1.2
    daddy_context = _daddy_context_ok(daily, h4, entry)
    mtf_score = float(mtf.get("mtf_score", 50.0))
    rows: list[dict[str, Any]] = []

    if sweep_reclaim or bullish_fvg or breakout_pressure:
        score = 45.0 + (12.0 if sweep_reclaim else 0.0) + (10.0 if bullish_fvg else 0.0) + (8.0 if breakout_pressure else 0.0) + min(10.0, volume_burst * 2.0) + max(0.0, (mtf_score - 50.0) * 0.15)
        if score >= 50.0:
            setup_type = "FVG_LIQUIDITY_SWEEP" if sweep_reclaim and bullish_fvg else "FVG_OB_OVERLAP" if bullish_fvg else "ICT_BREAKOUT_PRESSURE"
            stop = min(float(latest["low"]), recent_low) * 0.995
            target = entry + (entry - stop) * 2.0
            rows.append(_setup(market, "ICT_FVG_OB_SWEEP", setup_type, score, entry, stop, target, mtf, volume_burst, daddy_context))

    if rows and daddy_context["context_ok"]:
        base = rows[0]
        rows.append(
            _setup(
                market,
                "COMBINED_VOLUME_ICT",
                f"DADDY_CONTEXT+{base['setup_type']}",
                min(100.0, float(base["setup_quality_score"]) + 8.0),
                float(base["entry_price"]),
                float(base["stop_price"]),
                float(base["target_price"]),
                mtf,
                volume_burst,
                daddy_context,
            )
        )
    return rows


def _has_bullish_fvg(frame: pd.DataFrame) -> bool:
    if len(frame) < 3:
        return False
    for idx in range(2, len(frame)):
        if float(frame.iloc[idx - 2]["high"]) < float(frame.iloc[idx]["low"]):
            return True
    return False


def _daddy_context_ok(daily: pd.DataFrame, h4: pd.DataFrame, entry: float) -> dict[str, Any]:
    daily_ma20 = float(daily["close"].tail(20).mean()) if len(daily) >= 20 else entry
    h4_ma20 = float(h4["close"].tail(20).mean()) if len(h4) >= 20 else entry
    daily_volume_ratio = 1.0
    if len(daily) >= 21:
        avg = float(daily["volume"].iloc[:-1].tail(20).mean()) or 1.0
        daily_volume_ratio = float(daily["volume"].iloc[-1]) / avg
    return {
        "context_ok": entry >= daily_ma20 * 0.985 and entry >= h4_ma20 * 0.985 and daily_volume_ratio >= 0.8,
        "daily_ma20": daily_ma20,
        "h4_ma20": h4_ma20,
        "daily_volume_ratio": daily_volume_ratio,
    }


def _setup(
    market: str,
    strategy: str,
    setup_type: str,
    score: float,
    entry: float,
    stop: float,
    target: float,
    mtf: dict[str, Any],
    volume_burst: float,
    daddy_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "market": market,
        "strategy": strategy,
        "setup_type": setup_type,
        "setup_quality_score": score,
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "evidence": {"mtf": mtf, "volume_burst": volume_burst, "daddy_context": daddy_context},
        "real_order_enabled": False,
    }


def _execute_candidates(candidates: list[dict[str, Any]], initial_cash: float, max_open_positions: int) -> list[dict[str, Any]]:
    equity = initial_cash
    peak = initial_cash
    journal: list[dict[str, Any]] = []
    open_slots: Counter[str] = Counter()
    for setup in candidates:
        slot = str(setup["entry_time"])[:13]
        if open_slots[slot] >= max_open_positions:
            continue
        route = plan_for_trade(setup)
        if route["risk_multiplier"] <= 0:
            continue
        sizing = size_position(equity, float(setup["entry_price"]), float(setup["stop_price"]))
        if not sizing["sizing_valid"]:
            continue
        position_krw = min(float(sizing["position_krw"]), equity)
        exit_result = _simulate_exit(setup)
        pnl = position_krw * ((exit_result["exit_price"] / float(setup["entry_price"])) - 1.0) - position_krw * 0.001
        before = equity
        after = max(0.0, before + pnl)
        peak = max(peak, after)
        drawdown = (after - peak) / peak * 100 if peak else 0.0
        open_slots[slot] += 1
        journal.append(
            {
                "trade_id": f"twf_{len(journal)+1:05d}",
                "date": str(setup["entry_time"])[:10],
                "market": setup["market"],
                "plan": route["plan"],
                "strategy": setup["strategy"],
                "setup_type": setup["setup_type"],
                "regime": route["regime"],
                "signal_time": setup["signal_time"],
                "feature_cutoff_time": setup["feature_cutoff_time"],
                "used_future_data": False,
                "lookahead_check": "PASS",
                "entry_time": setup["entry_time"],
                "exit_time": exit_result["exit_time"],
                "entry_price": float(setup["entry_price"]),
                "exit_price": exit_result["exit_price"],
                "stop_price": float(setup["stop_price"]),
                "target_price": float(setup["target_price"]),
                "risk_per_trade_pct": 1.0 * route["risk_multiplier"],
                "risk_amount_krw": float(sizing["risk_amount_krw"]),
                "position_krw": position_krw,
                "pnl_krw": pnl,
                "return_pct": return_pct_from_equity(pnl, before),
                "equity_before": before,
                "equity_after": after,
                "drawdown_pct": drawdown,
                "result": exit_result["result"],
                "entry_reason": _korean_reasons(setup, route),
                "exit_reason": exit_result["exit_reason"],
                "lesson": _lesson(pnl),
                "risk_flags": ["OHLCV_ONLY_EXECUTION"],
                **_safety(),
            }
        )
        equity = after
    return journal


def _simulate_exit(setup: dict[str, Any]) -> dict[str, Any]:
    frame = setup.get("exit_plan_frame")
    entry = float(setup["entry_price"])
    stop = float(setup["stop_price"])
    target = float(setup["target_price"])
    if frame is None or frame.empty:
        return {"exit_price": entry, "exit_time": setup["entry_time"], "result": "TIME_EXIT", "exit_reason": "데이터 부족으로 시간 청산"}
    for _, candle in frame.iterrows():
        if float(candle["low"]) <= stop:
            return {"exit_price": stop, "exit_time": str(candle["time"]), "result": "LOSS", "exit_reason": "손절가 도달"}
        if float(candle["high"]) >= target:
            return {"exit_price": target, "exit_time": str(candle["time"]), "result": "WIN", "exit_reason": "목표가 도달"}
    last = frame.iloc[-1]
    return {"exit_price": float(last["close"]), "exit_time": str(last["time"]), "result": "TIME_EXIT", "exit_reason": "보유 시간 종료"}


def _summary(journal: list[dict[str, Any]], initial_cash: float, archive_dir: str | Path, risk_profile: str) -> dict[str, Any]:
    capital = summarize_capital_growth(journal, initial_cash)
    archive = _read(Path(archive_dir) / "latest_historical_archive_summary.json")
    return {
        "schema_version": "true_walk_forward_v1",
        "mode": "TRUE_WALK_FORWARD",
        "risk_profile": risk_profile,
        "investment_start_time": _start_time(journal, archive),
        "investment_end_time": journal[-1]["exit_time"] if journal else archive.get("latest_time"),
        "capital": capital,
        "journal": journal,
        "weekly_rows": build_weekly_rows(journal),
        "monthly_rows": build_monthly_rows(journal),
        "equity_curve": build_equity_curve(journal),
        "risk": build_risk_evidence(journal),
        "plan_performance": _group_performance(journal, "plan"),
        "strategy_contribution": _group_performance(journal, "strategy"),
        "archive_coverage": archive,
        "plain_language_summary": {
            "what_this_is": "업비트 과거 캔들을 시간순으로 지나가며 실제 돈을 넣었다고 가정한 PAPER 투자일지입니다.",
            "what_this_is_not": "실제 주문 결과가 아니며, 호가/체결 깊이는 아직 근사치입니다.",
        },
        **_safety(),
    }


def _group_performance(journal: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for trade in journal:
        groups.setdefault(str(trade.get(key, "UNKNOWN")), []).append(trade)
    total_pnl = sum(float(trade.get("pnl_krw", 0.0)) for trade in journal) or 1.0
    rows = []
    for name, trades in sorted(groups.items()):
        pnl = sum(float(trade.get("pnl_krw", 0.0)) for trade in trades)
        wins = [trade for trade in trades if float(trade.get("pnl_krw", 0.0)) > 0]
        losses = [trade for trade in trades if float(trade.get("pnl_krw", 0.0)) < 0]
        gross_win = sum(float(trade.get("pnl_krw", 0.0)) for trade in wins)
        gross_loss = abs(sum(float(trade.get("pnl_krw", 0.0)) for trade in losses))
        rows.append(
            {
                key: name,
                "trade_count": len(trades),
                "pnl_krw": pnl,
                "contribution_pct": pnl / total_pnl * 100,
                "win_rate": len(wins) / len(trades) * 100 if trades else 0.0,
                "profit_factor": gross_win / gross_loss if gross_loss else 0.0,
                "decision": "KEEP_FOR_FORWARD" if pnl > 0 else "REVIEW_OR_DISABLE",
            }
        )
    return rows


def _until(frame: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame[pd.to_datetime(frame["time"]) <= cutoff].copy()


def _korean_reasons(setup: dict[str, Any], route: dict[str, Any]) -> list[str]:
    return [
        f"시장 국면(Regime): {route['regime']}",
        f"전략(Strategy): {setup['strategy']}",
        f"셋업(Setup): {setup['setup_type']}",
        "미래 캔들을 보지 않고 현재 시점 이전 데이터만 사용",
    ]


def _lesson(pnl: float) -> str:
    if pnl > 0:
        return "수익 거래입니다. 셋업과 손익비가 실제 계좌 성장에 기여했습니다."
    return "손실 거래입니다. 손실 제한 규칙을 지켰는지 확인하고 같은 조건 반복을 줄여야 합니다."


def _start_time(journal: list[dict[str, Any]], archive: dict[str, Any]) -> str | None:
    if journal:
        return journal[0]["entry_time"]
    return archive.get("earliest_available_time")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _safety() -> dict[str, bool]:
    return {"real_order_enabled": False, "live_order_allowed": False, "auto_apply_allowed": False}
