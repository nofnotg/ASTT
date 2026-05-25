from __future__ import annotations


def build_ict_confluences(market: str, fvg_zones: list[dict], order_blocks: list[dict], sweeps: list[dict]) -> list[dict]:
    confluences = []
    for fvg in fvg_zones:
        if not fvg["zone_type"].startswith("BULLISH"):
            continue
        for ob in order_blocks:
            if not ob["zone_type"].startswith("BULLISH"):
                continue
            low = max(float(fvg["zone_low"]), float(ob["zone_low"]))
            high = min(float(fvg["zone_high"]), float(ob["zone_high"]))
            if low <= high:
                confluences.append(_conf("FVG_OB_OVERLAP", market, fvg["timeframe"], low, high, fvg, ob))
        for sweep in sweeps:
            if sweep["sweep_type"] == "BULLISH_LIQUIDITY_SWEEP":
                confluences.append(_conf("FVG_LIQUIDITY_SWEEP", market, fvg["timeframe"], fvg["zone_low"], fvg["zone_high"], fvg, sweep))
    return sorted(confluences, key=lambda row: row["quality_score"], reverse=True)[:8]


def _conf(kind: str, market: str, timeframe: str, low: float, high: float, a: dict, b: dict) -> dict:
    score = min(100.0, float(a.get("quality_score", 0.0)) * 0.55 + float(b.get("quality_score", 0.0)) * 0.45 + 10.0)
    return {
        "confluence_type": kind,
        "market": market,
        "timeframe": timeframe,
        "zone_low": low,
        "zone_high": high,
        "quality_score": score,
        "risk_level": "LOW" if score >= 75 else "MEDIUM" if score >= 55 else "HIGH",
    }
