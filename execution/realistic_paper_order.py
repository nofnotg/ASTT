from __future__ import annotations


def build_paper_order(candidate: dict, order_krw: float) -> dict:
    price = float(candidate["reference_price"])
    return {"market": candidate["market"], "candidate_id": candidate["candidate_id"], "candidate_source": candidate["candidate_source"], "order_krw": order_krw, "entry_time_ms": candidate["candidate_time_ms"], "target_price": price * (1 + float(candidate.get("expected_target_pct", 0.35)) / 100), "stop_price": price * (1 - float(candidate.get("expected_stop_pct", 0.20)) / 100), "real_order_enabled": False}
