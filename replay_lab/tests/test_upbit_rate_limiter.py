from adapters.upbit_rate_limiter import UpbitRateLimiter


def test_upbit_rate_limiter_records_calls():
    limiter = UpbitRateLimiter(max_calls_per_second=100)
    limiter.wait()
    limiter.wait()

    assert len(limiter._calls) == 2
