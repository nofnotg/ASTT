from __future__ import annotations


def estimate_krw_tick_size(price: float) -> float:
    if price >= 2_000_000:
        return 1_000.0
    if price >= 1_000_000:
        return 500.0
    if price >= 500_000:
        return 100.0
    if price >= 100_000:
        return 50.0
    if price >= 10_000:
        return 10.0
    if price >= 1_000:
        return 1.0
    if price >= 100:
        return 1.0
    if price >= 10:
        return 0.1
    return 0.01


def evaluate_tick_noise(start_price: float, peak_price: float, effective_return_pct: float) -> dict:
    tick_size = estimate_krw_tick_size(start_price)
    raw_move_ticks = abs(peak_price - start_price) / tick_size if tick_size else 0.0
    effective_move_price = max(0.0, start_price * effective_return_pct / 100)
    effective_move_ticks = effective_move_price / tick_size if tick_size else 0.0
    tick_noise_ratio = 1 / raw_move_ticks if raw_move_ticks else 1.0
    is_tick_noise = raw_move_ticks < 3 or effective_move_ticks < 2 or tick_noise_ratio > 0.5
    return {
        "tick_size": tick_size,
        "raw_move_ticks": raw_move_ticks,
        "effective_move_ticks": effective_move_ticks,
        "tick_noise_ratio": tick_noise_ratio,
        "is_tick_noise": is_tick_noise,
    }
