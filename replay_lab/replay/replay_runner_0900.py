from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

import pandas as pd

from app.config import TradingMode, get_settings
from decision.debate_engine import decide
from features.regime import calculate_regime
from personas import costa, iris, maggie, mr_k, rezo
from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.data_quality import evaluate_candles
from replay_lab.data.market_universe import top_markets
from replay_lab.data.replay_data_provider import ReplayDataProvider
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.replay.replay_session import ReplaySessionConfig


def _dt(config: ReplaySessionConfig, hhmm: str) -> datetime:
    hour, minute = [int(part) for part in hhmm.split(":")]
    return datetime.combine(config.date_kst, datetime.min.time()).replace(hour=hour, minute=minute)


class ReplayRunner0900:
    def __init__(self, provider: ReplayDataProvider, clock: ReplayClock | None = None) -> None:
        self.provider = provider
        self.clock = clock or provider.clock
        self.settings = get_settings(TRADING_MODE=TradingMode.PAPER, UPBIT_ACCESS_KEY="", UPBIT_SECRET_KEY="")

    def run(self, config: ReplaySessionConfig, top_market_limit: int | None = None) -> dict:
        self.clock.set(_dt(config, config.scan_time))
        markets = config.markets
        if top_market_limit:
            markets = top_markets(self.provider, markets, self.clock.current_time_kst, top_market_limit)
        session_rows = []
        persona_rows = []
        decision_rows = []
        trade_rows = []
        snapshot_rows = []
        for market in markets:
            result = self._run_market(config, market)
            session_rows.append(result["session"])
            persona_rows.extend(result["persona_scores"])
            decision_rows.append(result["decision"])
            if result["trade"]:
                trade_rows.append(result["trade"])
            snapshot_rows.extend(result["snapshots"])
        return {
            "session_results": pd.DataFrame(session_rows),
            "persona_scores": pd.DataFrame(persona_rows),
            "decisions": pd.DataFrame(decision_rows),
            "paper_trades": pd.DataFrame(trade_rows),
            "feature_snapshots": pd.DataFrame(snapshot_rows),
        }

    def _run_market(self, config: ReplaySessionConfig, market: str) -> dict:
        snapshots = []
        self.clock.set(_dt(config, config.pre_score_time))
        pre_candles = self.provider.get_candles(market, "1m", 80)
        quality = evaluate_candles(pre_candles.rename(columns={"time": "candle_time_kst"}))
        snapshots.append({"session_id": config.session_id, "market": market, "snapshot_time_kst": self.clock.current_time_kst.isoformat(), "features_json": {"data_quality": quality}})

        self.clock.advance_to(_dt(config, config.decision_time))
        candles = self.provider.get_candles(market, "1m", 80)
        trades = self.provider.get_trade_proxy(market, self.clock.current_time_kst)
        regime = calculate_regime(candles)
        price = float(candles["close"].iloc[-1]) if not candles.empty else 0.0
        context = {
            "market": market,
            "candles": candles,
            "trades": trades,
            "regime": regime,
            "price": price,
            "risk_reward": 1.8,
            "spread_pct": 0.1,
            "daily_loss_pct": 0.0,
            "open_positions": 0,
            "krw_amount": self.settings.min_order_krw,
            "btc_shock": regime.get("state") == "bearish",
            "data_quality_warning": "LOW_QUALITY" if quality["quality"] == "LOW_QUALITY" else None,
        }
        results = [
            mr_k.analyze(context),
            maggie.analyze(context),
            rezo.analyze(context),
            costa.analyze(context, self.settings),
            iris.analyze(context, self.settings),
        ]
        decision = decide(market, results, self.settings)
        persona_rows = [
            {
                "session_id": config.session_id,
                "date_kst": config.date_kst.isoformat(),
                "market": market,
                "persona": item.persona_name,
                "score": item.score,
                "decision": item.decision,
                "veto": item.veto,
                "veto_reason": item.veto_reason,
                "reasons": item.reasons,
                "warnings": item.warnings,
            }
            for item in results
        ]
        decision_row = {
            "session_id": config.session_id,
            "date_kst": config.date_kst.isoformat(),
            "market": market,
            "decision_time_kst": self.clock.current_time_kst.isoformat(),
            "entry_time_kst": _dt(config, config.entry_time).isoformat() if config.entry_time else self.clock.current_time_kst.isoformat(),
            "target_window_end_time_kst": _dt(config, config.target_window_end_time).isoformat(),
            "trade_end_time_kst": _dt(config, config.trade_end_time).isoformat(),
            "strategy_label": config.strategy_label,
            "day_type": "weekend" if config.date_kst.weekday() >= 5 else "weekday",
            "final_score": decision.final_score,
            "final_decision": decision.decision,
            "vetoed": decision.vetoed,
            "veto_reason": decision.veto_reason,
            "reasons": decision.reasons,
            "no_entry_reason": self._no_entry_reason(decision, results, quality),
        }
        trade_row = None
        if decision.decision == "ENTER" and not candles.empty:
            entry_at = _dt(config, config.entry_time) if config.entry_time else self.clock.current_time_kst
            self.clock.advance_to(_dt(config, config.trade_end_time))
            outcome = self.provider.get_candles(market, "1s", 4500)
            fill_timeframe = "1s"
            if outcome.empty:
                outcome = self.provider.get_candles(market, "1m", 80)
                fill_timeframe = "1m"
            outcome = outcome[outcome["time"] >= pd.Timestamp(entry_at)]
            stop_loss = price * 0.985
            take_profit = price * 1.015
            fill = simulate_long_trade(outcome, price, stop_loss, take_profit)
            trade_row = {
                "session_id": config.session_id,
                "date_kst": config.date_kst.isoformat(),
                "market": market,
                "decision_time_kst": _dt(config, config.decision_time).isoformat(),
                "entry_time_kst": entry_at.isoformat(),
                "target_window_end_time_kst": _dt(config, config.target_window_end_time).isoformat(),
                "trade_end_time_kst": _dt(config, config.trade_end_time).isoformat(),
                "strategy_label": config.strategy_label,
                "day_type": "weekend" if config.date_kst.weekday() >= 5 else "weekday",
                "fill_timeframe": fill_timeframe,
                **asdict(fill),
            }
        return {
            "session": {
                "session_id": config.session_id,
                "date_kst": config.date_kst.isoformat(),
                "market": market,
                "scan_time": config.scan_time,
                "pre_score_time": config.pre_score_time,
                "decision_time": config.decision_time,
                "entry_time": config.entry_time or config.decision_time,
                "target_window_end_time": config.target_window_end_time,
                "trade_end_time": config.trade_end_time,
                "strategy_label": config.strategy_label,
                "day_type": "weekend" if config.date_kst.weekday() >= 5 else "weekday",
                "candidate": not pre_candles.empty,
                "data_quality": quality["quality"],
            },
            "persona_scores": persona_rows,
            "decision": decision_row,
            "trade": trade_row,
            "snapshots": snapshots,
        }

    def _no_entry_reason(self, decision, persona_results: list, quality: dict) -> str:
        if decision.decision == "ENTER":
            return ""
        if decision.vetoed:
            return f"Iris veto: {decision.veto_reason or 'risk guard'}"
        if quality.get("quality") == "LOW_QUALITY":
            return "data quality low"
        weak = sorted(persona_results, key=lambda item: item.score)
        if weak:
            item = weak[0]
            return f"{item.persona_name} score low ({item.score:.1f})"
        return f"final score below entry threshold ({decision.final_score:.1f})"

