from __future__ import annotations

from statistics import pstdev


def attach_vwap_bands(rows: list[dict], window: int = 20, multipliers: tuple[float, ...] = (1.0, 2.0, 3.0)) -> list[dict]:
    out = []
    closes: list[float] = []
    for row in rows:
        close = float(row.get("close", row.get("price", 0.0)) or 0.0)
        closes.append(close)
        sample = closes[-window:]
        sigma = pstdev(sample) if len(sample) > 1 else 0.0
        base = float(row.get("daily_anchored_vwap", row.get("rolling_vwap_24h", close)) or close)
        banded = {**row}
        for m in multipliers:
            key = str(int(m))
            banded[f"vwap_band_upper_{key}"] = base + sigma * m
            banded[f"vwap_band_lower_{key}"] = base - sigma * m
        banded["band_extension_score"] = abs((close - base) / sigma) if sigma else 0.0
        banded["band_position"] = "ABOVE" if close > base else "BELOW" if close < base else "ON_VWAP"
        out.append(banded)
    return out
