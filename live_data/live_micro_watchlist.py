from __future__ import annotations


def build_live_micro_watchlist(static_markets=None, top_n: int = 20, candidate_markets=None, include_btc_eth: bool = True) -> list[str]:
    markets = []
    if include_btc_eth:
        markets.extend(["KRW-BTC", "KRW-ETH"])
    markets.extend(static_markets or [])
    markets.extend(candidate_markets or [])
    deduped = []
    for market in markets:
        if market and market not in deduped:
            deduped.append(market)
    return deduped[: max(1, top_n)]
