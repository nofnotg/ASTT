from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class UpbitRateLimitError(RuntimeError):
    pass


class UpbitTemporaryRateLimit(RuntimeError):
    pass


@dataclass
class SimpleRateLimiter:
    rps: int
    _calls: list[float] = field(default_factory=list)

    def wait(self) -> None:
        now = time.monotonic()
        self._calls = [ts for ts in self._calls if now - ts < 1.0]
        if len(self._calls) >= self.rps:
            sleep_for = 1.0 - (now - self._calls[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._calls.append(time.monotonic())


class UpbitClient:
    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None) -> None:
        self.settings = settings or get_settings()
        self.session = session or requests.Session()
        self.base_url = self.settings.upbit_base_url.rstrip("/")
        self.timeout = 10
        self.rate_limiter = SimpleRateLimiter(max(1, self.settings.upbit_quotation_rps_limit))

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.rate_limiter.wait()
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        remaining = response.headers.get("Remaining-Req")
        if remaining:
            logger.debug("upbit Remaining-Req: %s", remaining)
        if response.status_code == 418:
            raise UpbitRateLimitError("Upbit returned 418: requests are temporarily blocked")
        if response.status_code == 429:
            time.sleep(self.settings.rate_limit_backoff_seconds)
            raise UpbitTemporaryRateLimit("Upbit returned 429: rate limit exceeded")
        response.raise_for_status()
        return response.json()

    def get_markets(self) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/market/all", params={"isDetails": "true"})

    def get_krw_markets(self) -> list[str]:
        markets = self.get_markets()
        return [item["market"] for item in markets if item.get("market", "").startswith("KRW-")]

    def get_ticker(self, markets: list[str]) -> list[dict[str, Any]]:
        if not markets:
            return []
        return self._request("GET", "/v1/ticker", params={"markets": ",".join(markets)})

    def get_orderbook(self, markets: list[str]) -> list[dict[str, Any]]:
        if not markets:
            return []
        return self._request("GET", "/v1/orderbook", params={"markets": ",".join(markets)})

    def get_candles_minutes(self, market: str, unit: int, count: int = 200) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/candles/minutes/{unit}", params={"market": market, "count": count})

    def get_candles_days(self, market: str, count: int = 200) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/candles/days", params={"market": market, "count": count})

    def get_recent_trades(self, market: str, count: int = 100) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/trades/ticks", params={"market": market, "count": count})

