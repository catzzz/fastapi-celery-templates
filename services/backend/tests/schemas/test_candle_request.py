from apis.schemas.candle_request import CandleRequest


def test_candle_request():
    """Test CandleRequest creation and attributes."""
    request = CandleRequest(
        sec_type="STK", symbol="AAPL", bar_size="1 min", from_time=1633027200000, to_time=1633027260000
    )

    assert request.sec_type == "STK"
    assert request.symbol == "AAPL"
    assert request.bar_size == "1 min"
    assert request.from_time == 1633027200000
    assert request.to_time == 1633027260000
