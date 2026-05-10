from __future__ import annotations

from datetime import datetime

from replay_lab.data.replay_data_provider import ReplayDataProvider


def top_markets(provider: ReplayDataProvider, markets: list[str], at_time: datetime, limit: int) -> list[str]:
    ranked = []
    for market in markets:
        ticker = provider.get_ticker_snapshot(market, at_time)
        ranked.append((market, float(ticker.get("acc_trade_price_24h") or ticker.get("trade_price") or 0)))
    return [market for market, _ in sorted(ranked, key=lambda item: item[1], reverse=True)[:limit]]

