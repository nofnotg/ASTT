from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

from btcd.btcd_validation import validate_dominance_record


COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"


def fetch_coingecko_global(timeout_seconds: int = 10) -> dict[str, Any]:
    request = Request(COINGECKO_GLOBAL_URL, headers={"User-Agent": "ASTT-Research/1.0"})
    fetched_at = datetime.now(timezone.utc).isoformat()
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    data = payload.get("data") or {}
    percentage = (data.get("market_cap_percentage") or {}).get("btc")
    record = {
        "source": "coingecko",
        "dominance": _float(percentage),
        "market_cap_usd": _float((data.get("total_market_cap") or {}).get("usd")),
        "volume_24h_usd": _float((data.get("total_volume") or {}).get("usd")),
        "fetched_at": fetched_at,
        "source_updated_at": fetched_at,
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
