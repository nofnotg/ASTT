from __future__ import annotations

import json

from btcd.coingecko_global_client import fetch_coingecko_global


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"data": {"market_cap_percentage": {"btc": 51.1}, "total_market_cap": {"usd": 1000}, "total_volume": {"usd": 10}}}).encode()


def test_coingecko_global_client_parses_btc_percentage(monkeypatch):
    monkeypatch.setattr("btcd.coingecko_global_client.urlopen", lambda *args, **kwargs: _Response())
    record = fetch_coingecko_global()
    assert record["source"] == "coingecko"
    assert record["dominance"] == 51.1
