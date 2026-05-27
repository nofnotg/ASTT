from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

from btcd.btcd_validation import validate_dominance_record


COINPAPRIKA_GLOBAL_URL = "https://api.coinpaprika.com/v1/global"


def fetch_coinpaprika_global(timeout_seconds: int = 10) -> dict[str, Any]:
    request = Request(COINPAPRIKA_GLOBAL_URL, headers={"User-Agent": "ASTT-Research/1.0"})
    fetched_at = datetime.now(timezone.utc).isoformat()
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    record = {
        "source": "coinpaprika",
        "dominance": _float(payload.get("bitcoin_dominance_percentage")),
        "market_cap_usd": _float(payload.get("market_cap_usd")),
        "volume_24h_usd": _float(payload.get("volume_24h_usd")),
        "fetched_at": fetched_at,
        "source_updated_at": payload.get("last_updated") or payload.get("updated_at") or fetched_at,
    }
    record["validation"] = validate_dominance_record(record)
    return record


def _float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
