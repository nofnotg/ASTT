from __future__ import annotations

import argparse
from datetime import datetime

import pandas as pd

from app.config import TradingMode, get_settings
from data.storage import Storage
from decision.debate_engine import decide
from execution.order_intent import create_entry_intent
from execution.risk_guard import assert_can_create_intent
from execution.upbit_order_test import OrderTestBroker
from feedback.performance import generate_daily_report
from features.regime import calculate_regime
from personas import costa, iris, maggie, mr_k, rezo
from simulation.paper_broker import PaperBroker


def replay_candles() -> pd.DataFrame:
    rows = []
    price = 1000.0
    for i in range(40):
        open_price = price
        close = price * (1 + (0.001 if i > 28 else 0.0002))
        high_multiplier = 1.03 if i == 39 else 1.004
        high = max(open_price, close) * high_multiplier
        low = min(open_price, close) * 0.997
        volume = 100 + (600 if i == 39 else 260 if i in {24, 30, 31, 32} else i)
        rows.append({"open": open_price, "high": high, "low": low, "close": close, "volume": volume, "time": f"09:{i:02d}:00"})
        price = close
    return pd.DataFrame(rows)


def replay_trades() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ask_bid": "BID", "trade_volume": 3.0},
            {"ask_bid": "BID", "trade_volume": 2.0},
            {"ask_bid": "ASK", "trade_volume": 1.0},
        ]
    )


def run_replay(mode: TradingMode = TradingMode.PAPER, with_order_test: bool = False) -> dict:
    settings = get_settings(TRADING_MODE=mode)
    storage = Storage(settings)
    market = "KRW-BTC"
    candles = replay_candles()
    trades = replay_trades()
    regime = calculate_regime(candles)
    price = float(candles["close"].iloc[-1])
    context = {
        "market": market,
        "candles": candles,
        "trades": trades,
        "regime": regime,
        "price": price,
        "risk_reward": 1.8,
        "spread_pct": 0.1,
        "daily_loss_pct": 0.0,
        "open_positions": storage.count_open_positions(),
        "krw_amount": settings.min_order_krw,
        "btc_shock": regime["state"] == "bearish",
    }
    results = [
        mr_k.analyze(context),
        maggie.analyze(context),
        rezo.analyze(context),
        costa.analyze(context, settings),
        iris.analyze(context, settings),
    ]
    decision = decide(market, results, settings)
    signal_id = storage.save_signal(decision)
    storage.save_persona_scores(results, signal_id=signal_id)
    submitted = None
    if decision.decision == "ENTER":
        assert_can_create_intent(decision)
        intent = create_entry_intent(signal_id, market, settings.min_order_krw, settings.trading_mode.value)
        if settings.trading_mode == TradingMode.ORDER_TEST:
            submitted = OrderTestBroker(settings, storage).submit(intent)
        else:
            submitted = PaperBroker(storage, settings).submit(intent, best_ask=price)
            if with_order_test:
                OrderTestBroker(settings, storage).submit(intent)
    report = generate_daily_report(storage, settings, datetime.now().date().isoformat())
    return {"decision": decision.model_dump(), "submitted": submitted, "report": str(report)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ASTT 09:00 runner")
    parser.add_argument("--mode", choices=["paper", "order_test"], default="paper")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--with-order-test", action="store_true")
    parser.add_argument("--markets", default="KRW-BTC")
    args = parser.parse_args(argv)
    mode = TradingMode.ORDER_TEST if args.mode == "order_test" else TradingMode.PAPER
    if not args.replay:
        print("live schedule mode is not started in MVP CLI; use --replay for deterministic verification")
    result = run_replay(mode, with_order_test=args.with_order_test)
    print(f"runner ok: decision={result['decision']['decision']} score={result['decision']['final_score']} report={result['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
