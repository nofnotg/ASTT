from __future__ import annotations


def build_experiment_queue(primary_problem: str) -> list[str]:
    if primary_problem == "ENTER_0":
        return ["Collect high-volatility UPBIT_WS sessions", "Redesign micro candidate source", "Re-run entry discovery with balanced gate"]
    return ["Continue forward paper validation"]
