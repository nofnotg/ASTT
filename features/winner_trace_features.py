from __future__ import annotations


def summarize_winner_trace_features(traces: list[dict]) -> dict:
    windows = ["T_MINUS_10S", "T_MINUS_30S", "T_MINUS_60S", "T_MINUS_180S", "T_MINUS_300S"]
    result = {}
    for window in windows:
        rows = [trace.get("trace_windows", {}).get(window, {}) for trace in traces if trace.get("trace_windows", {}).get(window)]
        result[window] = {
            "avg_price_change_10s_pct": _avg(rows, "price_change_10s_pct"),
            "avg_buy_trade_ratio_10s": _avg(rows, "buy_trade_ratio_10s"),
            "avg_volume_burst_ratio_10s_vs_60s": _avg(rows, "volume_burst_ratio_10s_vs_60s"),
            "avg_orderbook_imbalance": _avg(rows, "orderbook_imbalance"),
            "notes": "GOOD/PARTIAL traces only" if rows else "NO_DATA",
        }
    return result


def _avg(rows: list[dict], key: str) -> float:
    vals = [float(row.get(key, 0.0)) for row in rows]
    return sum(vals) / len(vals) if vals else 0.0
