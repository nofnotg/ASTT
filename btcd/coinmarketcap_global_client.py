from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from btcd.btcd_validation import validate_dominance_record


CMC_GLOBAL_URL = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
CMC_GLOBAL_HISTORICAL_URL = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/historical"


def fetch_coinmarketcap_global(timeout_seconds: int = 10) -> dict[str, Any]:
    api_key = os.environ.get("CMC_API_KEY")
    if not api_key:
        return {
            "source": "coinmarketcap",
            "available": False,
            "reason": "CMC_API_KEY_NOT_SET",
            "validation": {"valid": False, "data_quality": "UNAVAILABLE", "reason": ["CMC_API_KEY_NOT_SET"]},
        }
    request = Request(CMC_GLOBAL_URL, headers={"X-CMC_PRO_API_KEY": api_key, "User-Agent": "ASTT-Research/1.0"})
    fetched_at = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "source": "coinmarketcap",
            "available": False,
            "reason": f"HTTP_{exc.code}",
            "error_message": _cmc_error_message(body),
            "validation": {"valid": False, "data_quality": "UNAVAILABLE", "reason": [f"HTTP_{exc.code}"]},
        }
    except Exception as exc:
        return {
            "source": "coinmarketcap",
            "available": False,
            "reason": type(exc).__name__,
            "validation": {"valid": False, "data_quality": "UNAVAILABLE", "reason": [type(exc).__name__]},
        }
    data = payload.get("data") or {}
    record = {
        "source": "coinmarketcap",
        "dominance": _float(data.get("btc_dominance")),
        "market_cap_usd": _float(data.get("quote", {}).get("USD", {}).get("total_market_cap")),
        "volume_24h_usd": _float(data.get("quote", {}).get("USD", {}).get("total_volume_24h")),
        "fetched_at": fetched_at,
        "source_updated_at": data.get("last_updated") or fetched_at,
    }
    record["validation"] = validate_dominance_record(record)
    return record


def fetch_cmc_btc_dominance_history(
    start: str = "2022-01-01T00:00:00Z",
    end: str | None = None,
    interval: str = "1d",
    timeout_seconds: int = 20,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    api_key = os.environ.get("CMC_API_KEY")
    if not api_key:
        return pd.DataFrame(), {
            "available": False,
            "source": "coinmarketcap",
            "reason": "CMC_API_KEY_NOT_SET",
            "notes": "CoinMarketCap historical requires CMC_API_KEY. The key value is never printed or saved.",
        }
    params = {
        "time_start": start,
        "interval": interval,
        "convert": "USD",
    }
    if end:
        params["time_end"] = end
    url = f"{CMC_GLOBAL_HISTORICAL_URL}?{urlencode(params)}"
    request = Request(url, headers={"X-CMC_PRO_API_KEY": api_key, "User-Agent": "ASTT-Research/1.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = _cmc_error_message(body)
        return pd.DataFrame(), {
            "available": False,
            "source": "coinmarketcap",
            "reason": f"HTTP_{exc.code}",
            "error_message": message,
            "notes": "CoinMarketCap historical request failed. API key was not printed.",
        }
    except Exception as exc:
        return pd.DataFrame(), {
            "available": False,
            "source": "coinmarketcap",
            "reason": type(exc).__name__,
            "notes": "CoinMarketCap historical request failed. API key was not printed.",
        }
    quotes = ((payload.get("data") or {}).get("quotes") or [])
    rows: list[dict[str, Any]] = []
    for quote in quotes:
        usd_quote = (quote.get("quote") or {}).get("USD") or {}
        rows.append(
            {
                "timestamp": quote.get("timestamp"),
                "btc_dominance_pct": _float(quote.get("btc_dominance")),
                "market_cap_usd": _float(usd_quote.get("total_market_cap") or quote.get("total_market_cap")),
                "volume_24h_usd": _float(usd_quote.get("total_volume_24h") or quote.get("total_volume_24h")),
                "source": "coinmarketcap",
                "source_updated_at": usd_quote.get("timestamp") or quote.get("timestamp"),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame, {
            "available": False,
            "source": "coinmarketcap",
            "reason": "NO_QUOTES_RETURNED",
            "notes": "CoinMarketCap historical returned no quotes for the requested range.",
        }
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame["btc_dominance_pct"] = pd.to_numeric(frame["btc_dominance_pct"], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "btc_dominance_pct"]).sort_values("timestamp")
    return frame, {
        "available": not frame.empty,
        "source": "coinmarketcap",
        "period": f"{frame['timestamp'].min()} ~ {frame['timestamp'].max()}" if not frame.empty else "unavailable",
        "coverage": f"{len(frame)} rows",
        "notes": "CoinMarketCap historical global metrics loaded. Plan limits may restrict actual period.",
    }


def _cmc_error_message(body: str) -> str:
    try:
        payload = json.loads(body)
        status = payload.get("status") or {}
        return str(status.get("error_message") or status.get("error_code") or "CMC_ERROR")
    except Exception:
        return body[:300]


def save_cmc_btc_dominance_history(
    output_path: str | Path = "data/external/btc_dominance_history.csv",
    start: str = "2022-01-01T00:00:00Z",
    end: str | None = None,
    interval: str = "1d",
) -> dict[str, Any]:
    frame, quality = fetch_cmc_btc_dominance_history(start=start, end=end, interval=interval)
    if frame.empty:
        return {"saved": False, "path": str(output_path), "quality": quality}
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return {"saved": True, "path": str(path), "rows": len(frame), "quality": quality}


def _float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
