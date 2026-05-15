import pytest

from adapters.upbit_client import UpbitClient, UpbitRateLimitError, UpbitTemporaryRateLimit
from app.config import get_settings


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.headers = {}
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return {}


class FakeSession:
    def __init__(self, code):
        self.code = code

    def request(self, *args, **kwargs):
        return FakeResponse(self.code)


def test_429_backoff(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    client = UpbitClient(settings=get_settings(TRADING_MODE="PAPER"), session=FakeSession(429))
    with pytest.raises(UpbitTemporaryRateLimit):
        client.get_markets()


def test_418_hard_stop():
    client = UpbitClient(settings=get_settings(TRADING_MODE="PAPER"), session=FakeSession(418))
    with pytest.raises(UpbitRateLimitError):
        client.get_markets()

