from shared.enums.bar_size import BarSize
from shared.enums.currency import Currency
from shared.enums.sec_type import SecType
from shared.schemas.candle_request import CandleRequest
from shared.schemas.contract_request import ExtendContractRequest


def test_candle_request():
    """Test CandleRequest creation and attributes."""
    request = CandleRequest(
        extend_contract_request=ExtendContractRequest(
            sec_type=SecType.STK,
            symbol="AAPL",
            currency=Currency.USD,
            bar_size=BarSize.ONE_MINUTE,
        ),
        from_time=1633027200000,
        to_time=1633027260000,
    )

    assert request.extend_contract_request.sec_type == SecType.STK
    assert request.extend_contract_request.symbol == "AAPL"
    assert request.extend_contract_request.bar_size == BarSize.ONE_MINUTE
    assert request.extend_contract_request.currency == Currency.USD
    assert request.from_time == 1633027200000
    assert request.to_time == 1633027260000
