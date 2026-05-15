from __future__ import annotations


def build_walk_forward_windows(days: int = 90) -> list[dict[str, int]]:
    if days < 45:
        raise ValueError("walk-forward requires at least 45 days")
    return [
        {"train_start": 1, "train_end": 30, "test_start": 31, "test_end": 45},
        {"train_start": 16, "train_end": 45, "test_start": 46, "test_end": 60},
        {"train_start": 31, "train_end": 60, "test_start": 61, "test_end": 75},
        {"train_start": 46, "train_end": 75, "test_start": 76, "test_end": min(days, 90)},
    ]

