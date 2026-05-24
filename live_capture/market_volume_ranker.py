from __future__ import annotations


DEFAULT_TOP_KRW_MARKETS = [
    "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-SUI", "KRW-DOGE", "KRW-ADA", "KRW-AVAX", "KRW-LINK", "KRW-TRX",
    "KRW-DOT", "KRW-NEAR", "KRW-BCH", "KRW-ETC", "KRW-MATIC", "KRW-SEI", "KRW-APT", "KRW-ARB", "KRW-STX", "KRW-HBAR",
    "KRW-ATOM", "KRW-ALGO", "KRW-SAND", "KRW-AXS", "KRW-MANA", "KRW-CELO", "KRW-FLOW", "KRW-IOTA", "KRW-IMX", "KRW-AAVE",
]


def rank_top_krw_markets(top_markets: int = 30) -> list[str]:
    return DEFAULT_TOP_KRW_MARKETS[:top_markets]
