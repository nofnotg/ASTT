from __future__ import annotations

import json

from btcd.coinpaprika_global_client import fetch_coinpaprika_global


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"bitcoin_dominance_percentage": 52.3, "market_cap_usd": 1000, "volume_24h_usd": 50}).encode()


def test_coinpaprika_global_client_parses_dominance(monkeypatch):
    monkeypatch.setattr("btcd.coinpaprika_global_client.urlopen", lambda *args, **kwargs: _Response())
    record = fetch_coinpaprika_global()
    assert record["source"] == "coinpaprika"
    assert record["dominance"] == 52.3
    assert record["validation"]["dominance_range_valid"] is True
