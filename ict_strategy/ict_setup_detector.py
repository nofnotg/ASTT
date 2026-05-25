from __future__ import annotations

import pandas as pd

from ict_strategy.fvg_detector import detect_fvg
from ict_strategy.ict_confluence_engine import build_ict_confluences
from ict_strategy.ict_setup_scorer import score_ict_setup
from ict_strategy.liquidity_sweep_detector import detect_liquidity_sweeps
from ict_strategy.order_block_detector import detect_order_blocks


def detect_ict_setup(market: str, h1: pd.DataFrame, m15: pd.DataFrame, mtf: dict) -> dict | None:
    base = h1 if h1 is not None and len(h1) >= 20 else m15
    fvg = detect_fvg(base, "1h")
    ob = detect_order_blocks(base, "1h")
    sweeps = detect_liquidity_sweeps(m15 if m15 is not None and len(m15) >= 20 else base)
    confluences = build_ict_confluences(market, fvg, ob, sweeps)
    if not confluences and fvg:
        confluences = [{"confluence_type": "FVG_ONLY", "market": market, "timeframe": "1h", "zone_low": fvg[-1]["zone_low"], "zone_high": fvg[-1]["zone_high"], "quality_score": fvg[-1]["quality_score"], "risk_level": "MEDIUM"}]
    if not confluences:
        return None
    conf = confluences[0]
    score = score_ict_setup(conf, float(mtf.get("mtf_score", 0.0)))
    if score < 45:
        return None
    close = float(base["close"].iloc[-1])
    stop = min(float(conf["zone_low"]) * 0.995, close * 0.97)
    target = close + (close - stop) * 1.8
    return {
        "market": market,
        "strategy": "ICT_FVG_OB_SWEEP",
        "setup_type": conf["confluence_type"],
        "setup_quality_score": score,
        "entry_price": close,
        "stop_price": stop,
        "target_price": target,
        "evidence": {"fvg": fvg[-3:], "order_blocks": ob[-3:], "sweeps": sweeps[-3:], "confluence": conf, "mtf": mtf},
        "real_order_enabled": False,
    }
