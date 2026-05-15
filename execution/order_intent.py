from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class OrderIntent(BaseModel):
    signal_id: int | None = None
    market: str
    side: str
    ord_type: str
    krw_amount: float | None = None
    price: float | None = None
    volume: float | None = None
    identifier: str = ""
    reason: str
    mode: str

    @model_validator(mode="after")
    def validate_order(self) -> "OrderIntent":
        if self.side not in {"bid", "ask"}:
            raise ValueError("side must be bid or ask")
        if self.ord_type not in {"price", "market", "limit"}:
            raise ValueError("ord_type must be price, market, or limit")
        if not self.identifier:
            seed = f"{self.signal_id}:{self.market}:{self.side}:{self.krw_amount}:{self.price}:{datetime.utcnow().isoformat(timespec='microseconds')}:{time.time_ns()}:{uuid.uuid4()}"
            digest = hashlib.sha256(seed.encode()).hexdigest()[:16]
            self.identifier = f"astt-{self.market}-{self.side}-{digest}"
        return self


def create_entry_intent(signal_id: int | None, market: str, krw_amount: float, mode: str, reason: str = "FinalDecision ENTER") -> OrderIntent:
    return OrderIntent(signal_id=signal_id, market=market, side="bid", ord_type="price", krw_amount=krw_amount, reason=reason, mode=mode)


def validate_min_order(intent: OrderIntent, min_order_krw: float) -> None:
    if intent.side == "bid" and (intent.krw_amount or 0) < min_order_krw:
        raise ValueError("order amount is below MIN_ORDER_KRW")
