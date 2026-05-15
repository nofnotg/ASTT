from __future__ import annotations

from app.config import Settings, TradingMode, get_settings
from execution.broker import Broker
from execution.order_intent import OrderIntent


class LiveBroker(Broker):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def submit(self, intent: OrderIntent, iris_veto: bool = False):
        if self.settings.trading_mode != TradingMode.LIVE:
            raise RuntimeError("Live order blocked: TRADING_MODE is not LIVE")
        if self.settings.live_trading_enabled is not True:
            raise RuntimeError("Live order blocked: LIVE_TRADING_ENABLED is not true")
        if iris_veto:
            raise RuntimeError("Live order blocked: Iris veto is true")
        print("[FINAL LIVE ORDER CHECK]")
        print(f"market={intent.market}")
        print(f"side={intent.side}")
        print(f"amount={intent.krw_amount}")
        print(f"risk=guarded")
        print(f"iris_veto={iris_veto}")
        print(f"mode={self.settings.trading_mode.value}")
        print(f"live_enabled={self.settings.live_trading_enabled}")
        raise NotImplementedError("Live order submission is intentionally not enabled in MVP")

