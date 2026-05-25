from __future__ import annotations

from mtf.mtf_context_builder import build_v6_mtf_context


def run_v6_mtf_context_generation(markets: str) -> dict:
    return build_v6_mtf_context(markets)
