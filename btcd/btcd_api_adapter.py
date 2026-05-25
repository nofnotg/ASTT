from __future__ import annotations

from typing import Any

import pandas as pd


def try_load_global_btcd_from_api() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Placeholder adapter.

    V6.6 does not fabricate global BTC dominance. If a future CMC/CoinGecko
    adapter is added, it must return actual historical dominance rows.
    """

    return pd.DataFrame(columns=["timestamp", "btc_dominance_pct", "source"]), {
        "available": False,
        "source": "api_unavailable",
        "notes": "No API adapter was activated; no fake BTC dominance data was generated.",
    }

