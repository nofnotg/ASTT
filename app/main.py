from __future__ import annotations

import argparse
import sys

from adapters.upbit_auth import UpbitAuth
from adapters.upbit_client import UpbitClient
from app.config import TradingMode, get_settings, safe_settings_summary
from data.storage import init_db


def check_public() -> int:
    settings = get_settings()
    client = UpbitClient(settings=settings)
    markets = client.get_krw_markets()
    ticker = client.get_ticker(["KRW-BTC"])
    orderbook = client.get_orderbook(["KRW-BTC"])
    print(f"public ok: krw_markets={len(markets)} ticker={bool(ticker)} orderbook={bool(orderbook)}")
    return 0


def check_auth() -> int:
    settings = get_settings()
    if not settings.has_upbit_keys:
        print("auth check skipped: UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY are required")
        return 2
    auth = UpbitAuth(settings)
    headers = auth.make_headers()
    print(f"auth header ok: {headers.get('Authorization', '').startswith('Bearer ')}")
    return 0


def run_mode(mode: str) -> int:
    mode_map = {
        "paper": TradingMode.PAPER,
        "order_test": TradingMode.ORDER_TEST,
        "live_disabled": TradingMode.LIVE_DISABLED,
    }
    settings = get_settings(TRADING_MODE=mode_map[mode])
    init_db(settings)
    print(f"ASTT ready: {safe_settings_summary(settings)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ASTT Upbit paper trading MVP")
    parser.add_argument("--check-public", action="store_true")
    parser.add_argument("--check-auth", action="store_true")
    parser.add_argument("--mode", choices=["paper", "order_test", "live_disabled"])
    args = parser.parse_args(argv)

    try:
        if args.check_public:
            return check_public()
        if args.check_auth:
            return check_auth()
        if args.mode:
            return run_mode(args.mode)
        parser.print_help()
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

