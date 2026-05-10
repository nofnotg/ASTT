from __future__ import annotations

from datetime import datetime

from app.config import Settings, get_settings
from data.storage import Storage
from execution.broker import Broker
from execution.order_intent import OrderIntent, validate_min_order
from simulation.fill_model import conservative_ask_fill, conservative_bid_fill


class PaperBroker(Broker):
    def __init__(self, storage: Storage | None = None, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.storage = storage or Storage(self.settings)

    def submit(self, intent: OrderIntent, best_ask: float | None = None, best_bid: float | None = None):
        validate_min_order(intent, self.settings.min_order_krw)
        order_intent_id = self.storage.save_order_intent(intent, status="PAPER_SUBMITTED")
        if intent.side == "bid":
            return self._buy(intent, order_intent_id, best_ask or intent.price or 0)
        return self._sell(intent, order_intent_id, best_bid or intent.price or 0)

    def _buy(self, intent: OrderIntent, order_intent_id: int, best_ask: float):
        if best_ask <= 0:
            raise ValueError("best_ask is required for paper buy")
        fill_price, slippage_per_unit = conservative_bid_fill(best_ask, self.settings.default_slippage_pct)
        gross = float(intent.krw_amount or 0)
        fee = gross * self.settings.taker_fee_pct / 100
        volume = max(0.0, (gross - fee) / fill_price)
        position_id = self.storage.add_position(intent.market, fill_price, volume, gross)
        self.storage.add_paper_trade(
            position_id=position_id,
            market=intent.market,
            side="bid",
            price=fill_price,
            volume=volume,
            fee_krw=fee,
            slippage_krw=slippage_per_unit * volume,
            realized_pnl_krw=0,
            realized_pnl_pct=0,
            reason=intent.reason,
        )
        return {"order_intent_id": order_intent_id, "position_id": position_id, "price": fill_price, "volume": volume}

    def _sell(self, intent: OrderIntent, order_intent_id: int, best_bid: float):
        position = self.storage.latest_open_position(intent.market)
        if not position:
            raise ValueError("no open paper position to sell")
        fill_price, slippage_per_unit = conservative_ask_fill(best_bid, self.settings.default_slippage_pct)
        volume = float(intent.volume or position.volume)
        proceeds = fill_price * volume
        fee = proceeds * self.settings.taker_fee_pct / 100
        pnl = proceeds - fee - (position.avg_price * volume)
        pnl_pct = pnl / (position.avg_price * volume) * 100 if position.avg_price and volume else 0.0
        position.status = "CLOSED"
        position.closed_at = datetime.utcnow()
        position.updated_at = datetime.utcnow()
        self.storage.update_position(position)
        self.storage.add_paper_trade(
            position_id=position.id,
            market=intent.market,
            side="ask",
            price=fill_price,
            volume=volume,
            fee_krw=fee,
            slippage_krw=slippage_per_unit * volume,
            realized_pnl_krw=pnl,
            realized_pnl_pct=pnl_pct,
            reason=intent.reason,
        )
        return {"order_intent_id": order_intent_id, "position_id": position.id, "price": fill_price, "volume": volume, "realized_pnl_krw": pnl}

