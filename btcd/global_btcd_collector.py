from __future__ import annotations

from typing import Any

from btcd.btcd_storage import save_btcd_record
from btcd.coingecko_global_client import fetch_coingecko_global
from btcd.coinmarketcap_global_client import fetch_coinmarketcap_global
from btcd.coinpaprika_global_client import fetch_coinpaprika_global


def collect_current_global_btcd(source: str = "coinpaprika", save: bool = True) -> dict[str, Any]:
    try:
        if source == "coingecko":
            record = fetch_coingecko_global()
        elif source == "coinmarketcap":
            record = fetch_coinmarketcap_global()
        else:
            record = fetch_coinpaprika_global()
        if save and record.get("dominance") is not None:
            record["storage"] = save_btcd_record(record)
        return record
    except Exception as exc:
        return {
            "source": source,
            "available": False,
            "reason": type(exc).__name__,
            "validation": {"valid": False, "data_quality": "UNAVAILABLE", "reason": [type(exc).__name__]},
        }
