from adapters.upbit_public_rest import UpbitPublicRest


class _Response:
    status_code = 200
    def raise_for_status(self): ...
    def json(self):
        return [{"market": "KRW-BTC", "candle_date_time_utc": "2026-05-23T00:00:00", "candle_date_time_kst": "2026-05-23T09:00:00", "opening_price": 100, "high_price": 101, "low_price": 99, "trade_price": 100.5, "candle_acc_trade_volume": 1, "candle_acc_trade_price": 100, "timestamp": 1}]


class _Session:
    def __init__(self):
        self.params = None
    def get(self, url, params, timeout):
        self.params = params
        return _Response()


def test_upbit_public_rest_seconds_params_and_normalization():
    session = _Session()
    result = UpbitPublicRest(session=session).get_second_candles("KRW-BTC", count=10)

    assert session.params["market"] == "KRW-BTC"
    assert result[0]["trade_price"] == 100.5


def test_upbit_public_rest_old_range_returns_empty():
    result = UpbitPublicRest(session=_Session()).get_second_candles("KRW-BTC", to="2025-01-01T00:00:00")

    assert result == []
