from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from typing import Callable

import websocket

from app.config import Settings, get_settings
from data.storage import Storage

logger = logging.getLogger(__name__)


class UpbitWebSocketClient:
    def __init__(self, settings: Settings | None = None, storage: Storage | None = None) -> None:
        self.settings = settings or get_settings()
        self.storage = storage
        self._stop = threading.Event()

    def build_payload(self, markets: list[str], tick_types: list[str] | None = None) -> str:
        types = tick_types or ["ticker", "trade", "orderbook"]
        payload = [{"ticket": str(uuid.uuid4())}]
        payload.extend({"type": item_type, "codes": markets} for item_type in types)
        return json.dumps(payload)

    def run_forever(self, markets: list[str], on_event: Callable[[dict], None] | None = None) -> None:
        while not self._stop.is_set():
            ws = websocket.WebSocket()
            try:
                ws.connect(self.settings.upbit_ws_public_url, ping_interval=30)
                ws.send(self.build_payload(markets))
                while not self._stop.is_set():
                    raw = ws.recv()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    event = json.loads(raw)
                    if self.storage:
                        self.storage.save_tick(event, store_raw=self.settings.store_raw_ticks)
                        self.storage.purge_old_ticks(self.settings.tick_retention_hours)
                    if on_event:
                        on_event(event)
            except Exception as exc:
                logger.warning("upbit websocket reconnecting after error: %s", exc)
                time.sleep(2)
            finally:
                try:
                    ws.close()
                except Exception:
                    pass

    def stop(self) -> None:
        self._stop.set()

