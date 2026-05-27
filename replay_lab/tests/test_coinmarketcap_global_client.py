from __future__ import annotations

import json

import pytest

from btcd.coinmarketcap_global_client import fetch_cmc_btc_dominance_history, fetch_coinmarketcap_global


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"data": {"quotes": [{"timestamp": "2024-01-01T00:00:00Z", "btc_dominance": 52.0, "total_market_cap": 1000, "total_volume_24h": 50}]}}).encode()


class _LatestResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(
            {
                "data": {
                    "btc_dominance": 57.5,
                    "last_updated": "2026-05-27T00:00:00.000Z",
                    "quote": {"USD": {"total_market_cap": 3000, "total_volume_24h": 200}},
                }
            }
        ).encode()


class _NestedHistoricalResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(
            {
                "data": {
                    "quotes": [
                        {
                            "timestamp": "2024-01-01T00:00:00Z",
                            "btc_dominance": 52.0,
                            "quote": {
                                "USD": {
                                    "total_market_cap": 1000,
                                    "total_volume_24h": 50,
                                    "timestamp": "2024-01-01T00:02:00Z",
                                }
                            },
                        }
                    ]
                }
            }
        ).encode()


def test_cmc_history_requires_key(monkeypatch):
    monkeypatch.delenv("CMC_API_KEY", raising=False)
    frame, quality = fetch_cmc_btc_dominance_history()
    assert frame.empty
    assert quality["reason"] == "CMC_API_KEY_NOT_SET"


def test_cmc_history_parses_quotes_without_printing_key(monkeypatch):
    monkeypatch.setenv("CMC_API_KEY", "secret-value-not-output")
    monkeypatch.setattr("btcd.coinmarketcap_global_client.urlopen", lambda *args, **kwargs: _Response())
    frame, quality = fetch_cmc_btc_dominance_history(start="2024-01-01T00:00:00Z", end="2024-01-02T00:00:00Z")
    assert len(frame) == 1
    assert float(frame.iloc[0]["btc_dominance_pct"]) == 52.0
    assert "secret-value-not-output" not in str(quality)


def test_cmc_latest_parses_basic_plan_endpoint_without_printing_key(monkeypatch):
    monkeypatch.setenv("CMC_API_KEY", "secret-value-not-output")
    monkeypatch.setattr("btcd.coinmarketcap_global_client.urlopen", lambda *args, **kwargs: _LatestResponse())
    record = fetch_coinmarketcap_global()
    assert record["dominance"] == 57.5
    assert record["market_cap_usd"] == 3000
    assert record["volume_24h_usd"] == 200
    assert "secret-value-not-output" not in str(record)


def test_cmc_history_parses_nested_quote_metrics(monkeypatch):
    monkeypatch.setenv("CMC_API_KEY", "secret-value-not-output")
    monkeypatch.setattr("btcd.coinmarketcap_global_client.urlopen", lambda *args, **kwargs: _NestedHistoricalResponse())
    frame, quality = fetch_cmc_btc_dominance_history(start="2024-01-01T00:00:00Z", end="2024-01-02T00:00:00Z")
    assert len(frame) == 1
    assert float(frame.iloc[0]["market_cap_usd"]) == 1000.0
    assert float(frame.iloc[0]["volume_24h_usd"]) == 50.0
    assert "secret-value-not-output" not in str(quality)


def test_cmc_history_reports_plan_block_without_key_leak(monkeypatch):
    class _HTTP403(Exception):
        pass

    from urllib.error import HTTPError

    monkeypatch.setenv("CMC_API_KEY", "secret-value-not-output")

    def blocked(*args, **kwargs):
        raise HTTPError(
            url="https://example.test",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=type("Body", (), {"read": lambda self: json.dumps({"status": {"error_message": "plan blocked"}}).encode()})(),
        )

    monkeypatch.setattr("btcd.coinmarketcap_global_client.urlopen", blocked)
    frame, quality = fetch_cmc_btc_dominance_history()
    assert frame.empty
    assert quality["reason"] == "HTTP_403"
    assert quality["error_message"] == "plan blocked"
    assert "secret-value-not-output" not in str(quality)
