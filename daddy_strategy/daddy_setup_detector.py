from __future__ import annotations

import pandas as pd

from daddy_strategy.fibonacci_pullback_engine import detect_fibonacci_pullback
from daddy_strategy.ma20_engine import analyze_ma20
from daddy_strategy.neckline_engine import detect_neckline
from daddy_strategy.sr_flip_engine import detect_sr_flip
from daddy_strategy.volume_truth_engine import analyze_volume_truth
from daddy_strategy.daddy_setup_scorer import score_daddy_setup


def detect_daddy_setup(market: str, daily: pd.DataFrame, h4: pd.DataFrame, h1: pd.DataFrame, mtf: dict) -> dict | None:
    base = h1 if h1 is not None and len(h1) >= 30 else daily
    volume = analyze_volume_truth(base)
    ma20 = analyze_ma20(daily)
    neckline = detect_neckline(h4 if h4 is not None and len(h4) >= 30 else daily)
    sr_flip = detect_sr_flip(base)
    fib = detect_fibonacci_pullback(h4 if h4 is not None and len(h4) >= 30 else daily)
    score = score_daddy_setup(volume, ma20, neckline, sr_flip, fib, float(mtf.get("mtf_score", 0.0)))
    if score < 45:
        return None
    close = float(base["close"].iloc[-1])
    stop = min(float(base["low"].tail(10).min()), close * 0.97)
    target = close + (close - stop) * 1.8
    return {
        "market": market,
        "strategy": "DADDY_VOLUME_NECKLINE",
        "setup_type": _setup_type(volume, neckline, sr_flip, fib),
        "setup_quality_score": score,
        "entry_price": close,
        "stop_price": stop,
        "target_price": target,
        "evidence": {"volume": volume, "ma20": ma20, "neckline": neckline, "sr_flip": sr_flip, "fib": fib, "mtf": mtf},
        "real_order_enabled": False,
    }


def _setup_type(volume: dict, neckline: dict, sr_flip: dict, fib: dict) -> str:
    if sr_flip.get("sr_flip_state") == "RETEST_HOLD":
        return "SR_FLIP_RETEST_VOLUME"
    if neckline.get("neckline_state") in {"BREAKOUT_RETEST_AREA", "NEAR_NECKLINE"}:
        return "NECKLINE_VOLUME_SETUP"
    if fib.get("fib_state") == "FIB_REACTION_ZONE":
        return "FIB_PULLBACK_VOLUME"
    return volume.get("volume_signal", "DADDY_VOLUME_SETUP")
