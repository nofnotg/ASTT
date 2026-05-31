from __future__ import annotations


class LiveOrderAdapterStub:
    def buy(self, *_args, **_kwargs) -> None:
        raise RuntimeError("LIVE_ORDER_DISABLED")

    def sell(self, *_args, **_kwargs) -> None:
        raise RuntimeError("LIVE_ORDER_DISABLED")

    def cancel(self, *_args, **_kwargs) -> None:
        raise RuntimeError("LIVE_ORDER_DISABLED")
