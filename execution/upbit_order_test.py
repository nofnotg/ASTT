from __future__ import annotations

import json
import time

import requests

from adapters.upbit_auth import UpbitAuth
from app.config import Settings, TradingMode, get_settings
from data.storage import Storage
from execution.broker import Broker
from execution.order_intent import OrderIntent


class OrderTestBroker(Broker):
    def __init__(self, settings: Settings | None = None, storage: Storage | None = None, session: requests.Session | None = None) -> None:
        self.settings = settings or get_settings()
        self.storage = storage or Storage(self.settings)
        self.session = session or requests.Session()
        self.auth = UpbitAuth(self.settings)

    def submit(self, intent: OrderIntent):
        if not self.settings.order_test_enabled:
            raise RuntimeError("orders/test blocked: ORDER_TEST_ENABLED is false")
        if self.settings.trading_mode not in {TradingMode.ORDER_TEST, TradingMode.LIVE_DISABLED, TradingMode.PAPER}:
            raise RuntimeError("orders/test blocked in current mode")
        if not self.settings.has_upbit_keys:
            raise RuntimeError("orders/test requires UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY")
        order_intent_id = self.storage.save_order_intent(intent, status="ORDER_TEST_SUBMITTED")
        payload = self._payload(intent)
        try:
            response = self._post(payload)
            self.storage.save_order_test_result(order_intent_id, intent.market, payload, response, None, "SUCCESS")
            return response
        except Exception as exc:
            error = {"message": str(exc)}
            self.storage.save_order_test_result(order_intent_id, intent.market, payload, None, error, "ERROR")
            raise

    def _payload(self, intent: OrderIntent) -> dict:
        payload = {"market": intent.market, "side": intent.side, "ord_type": intent.ord_type, "identifier": intent.identifier}
        if intent.price is not None:
            payload["price"] = str(intent.price)
        if intent.volume is not None:
            payload["volume"] = str(intent.volume)
        if intent.krw_amount is not None and intent.ord_type == "price":
            payload["price"] = str(intent.krw_amount)
        return payload

    def _post(self, payload: dict) -> dict:
        url = self.settings.upbit_base_url.rstrip("/") + "/v1/orders/test"
        headers = self.auth.make_headers(payload)
        for attempt in range(2):
            response = self.session.post(url, data=payload, headers=headers, timeout=10)
            if response.status_code == 429 and attempt == 0:
                time.sleep(self.settings.rate_limit_backoff_seconds)
                continue
            if response.status_code == 418:
                raise RuntimeError("Upbit returned 418: order API temporarily blocked")
            if response.status_code >= 400:
                try:
                    body = response.json()
                except json.JSONDecodeError:
                    body = {"raw": response.text}
                error_name = body.get("error", {}).get("name") if isinstance(body.get("error"), dict) else None
                raise RuntimeError(error_name or f"orders/test failed: {response.status_code}")
            return response.json()
        raise RuntimeError("orders/test failed after retry")

