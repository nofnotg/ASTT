from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daddy_strategy.daddy_setup_detector import detect_daddy_setup
from ict_strategy.ict_setup_detector import detect_ict_setup
from market_data.ohlcv_store import OHLCVStore
from risk.risk_reward_calculator import calculate_risk_reward
from strategy_engine.setup_ranker import rank_setups


def build_v6_strategy_setups(strategy: str = "COMBINED_VOLUME_ICT", store: OHLCVStore | None = None) -> dict[str, Any]:
    store = store or OHLCVStore()
    mtf = _read(Path("docs/reports/latest_v6_mtf_summary.json"))
    contexts = mtf.get("contexts", [])
    setups = []
    for ctx in contexts:
        market = ctx["market"]
        daily = store.load("1d", market)
        h4 = store.load("4h", market)
        h1 = store.load("1h", market)
        m15 = store.load("15m", market)
        daddy = detect_daddy_setup(market, daily, h4, h1, ctx)
        ict = detect_ict_setup(market, h1, m15, ctx)
        if strategy == "DADDY_VOLUME_NECKLINE" and daddy:
            setups.append(_with_rr(daddy))
        elif strategy == "ICT_FVG_OB_SWEEP" and ict:
            setups.append(_with_rr(ict))
        elif strategy == "COMBINED_VOLUME_ICT":
            if daddy and ict:
                setups.append(_combine(daddy, ict))
            elif daddy and daddy["setup_quality_score"] >= 60:
                setups.append(_with_rr(daddy))
            elif ict and ict["setup_quality_score"] >= 60:
                setups.append(_with_rr(ict))
    ranked = rank_setups([row for row in setups if row["risk_reward_ratio"] >= 1.2], 80)
    summary = {
        "schema_version": "v6",
        "strategy": strategy,
        "setup_count": len(ranked),
        "setups": ranked,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write(Path(f"replay_store/v6_strategy/{strategy.lower()}_setups.json"), summary)
    return summary


def _with_rr(setup: dict) -> dict:
    rr = calculate_risk_reward(setup["entry_price"], setup["stop_price"], setup["target_price"])
    return {**setup, "risk_reward_ratio": rr, "real_order_enabled": False}


def _combine(daddy: dict, ict: dict) -> dict:
    entry = (float(daddy["entry_price"]) + float(ict["entry_price"])) / 2
    stop = min(float(daddy["stop_price"]), float(ict["stop_price"]))
    target = max(float(daddy["target_price"]), float(ict["target_price"]))
    score = min(100.0, daddy["setup_quality_score"] * 0.5 + ict["setup_quality_score"] * 0.5 + 12.0)
    return {
        "market": daddy["market"],
        "strategy": "COMBINED_VOLUME_ICT",
        "setup_type": f"{daddy['setup_type']}+{ict['setup_type']}",
        "setup_quality_score": score,
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "risk_reward_ratio": calculate_risk_reward(entry, stop, target),
        "evidence": {"daddy": daddy["evidence"], "ict": ict["evidence"]},
        "real_order_enabled": False,
    }


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
