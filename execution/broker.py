from __future__ import annotations

from execution.order_intent import OrderIntent


class Broker:
    def submit(self, intent: OrderIntent):
        raise NotImplementedError

