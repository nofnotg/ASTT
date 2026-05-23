from live_data.upbit_ws_message_normalizer import normalize_upbit_orderbook_message, normalize_upbit_trade_message


def test_upbit_trade_message_normalize():
    result = normalize_upbit_trade_message({"type": "trade", "code": "KRW-BTC", "trade_price": 100, "trade_volume": 1, "ask_bid": "BID", "trade_timestamp": 123})

    assert result["data_source"] == "UPBIT_WS"
    assert result["market"] == "KRW-BTC"
    assert result["timestamp_ms"] == 123


def test_upbit_orderbook_message_normalize():
    result = normalize_upbit_orderbook_message({"type": "orderbook", "code": "KRW-BTC", "timestamp": 123, "orderbook_units": [{"ask_price": 101, "bid_price": 100, "ask_size": 1, "bid_size": 2}]})

    assert result["data_source"] == "UPBIT_WS"
    assert result["units"][0]["bid_size"] == 2
