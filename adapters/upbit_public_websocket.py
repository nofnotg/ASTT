from __future__ import annotations

import json
import time
import uuid
from typing import Callable

import websocket


WS_URL = "wss://api.upbit.com/websocket/v1"


def subscribe_upbit_ws(markets: list[str], types: list[str], duration_seconds: int, output_callback: Callable[[dict], None], format: str = "DEFAULT") -> dict:
    payload = [{"ticket": str(uuid.uuid4())}]
    for item_type in types:
        payload.append({"type": item_type, "codes": [m.upper() for m in markets]})
    if format:
        payload.append({"format": format})
    started = time.time()
    count = 0
    warnings: list[str] = []
    ws = websocket.WebSocket()
    try:
        ws.connect(WS_URL, timeout=10)
        ws.send(json.dumps(payload))
        while time.time() - started < duration_seconds:
            raw = ws.recv()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            event = json.loads(raw)
            output_callback(event)
            count += 1
    except Exception as exc:
        warnings.append(str(exc))
    finally:
        try:
            ws.close()
        except Exception:
            pass
    return {"message_count": count, "warnings": warnings}
