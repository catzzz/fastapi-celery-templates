from datetime import (
    datetime,
    timezone,
)
from unittest.mock import MagicMock

import pytest
from apis.enums.bar_size import BarSize
from apis.enums.currency import Currency
from apis.enums.exchange import Exchange
from apis.enums.sec_type import SecType
from apis.schemas.candle_request import CandleRequest
from apis.schemas.contract_request import ExtendContractRequest
from apis.ts_models.base_ts_model import TimeSeriesModelException
from apis.ts_models.ohlcv_candle_ts import (
    OhlcvCandleData,
    OhlcvCandleException,
    OhlcvCandleTS,
)


@pytest.fixture
def ohlcv_ts(mock_shared_redis_client):  # pylint: disable=unused-argument
    """Return an instance of OhlcvCandleTS."""
    return OhlcvCandleTS(debug=True)


@pytest.fixture
def sample_ohlcv_data():
    """Return a sample OhlcvCandleData."""
    return OhlcvCandleData(
        timestamp=int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000),
        open=100.0,
        high=105.0,
        low=98.0,
        close=103.0,
        volume=1000,
        wap=102.5,
        barcount=50,
    )


@pytest.fixture
def sample_extend_contract_request():
    """Return a sample ExtendContractRequest."""
    return ExtendContractRequest(
        sec_type=SecType.STK,
        symbol="AAPL",
        currency=Currency.USD,
        exchange=Exchange.SMART,
        bar_size=BarSize.ONE_MINUTE,
    )


@pytest.fixture
def sample_candle_data():
    """Return sample candle data."""
    return [
        (1609459200000, "100.0,105.0,98.0,103.0,1000,102.5,50"),
        (1609459260000, "103.0,106.0,102.0,104.0,1200,103.5,60"),
    ]


def test_get_key(ohlcv_ts, sample_extend_contract_request):
    """Test the get_key method."""
    result = ohlcv_ts.get_key(sample_extend_contract_request)
    expected_key = "candle_ts:stk:usd:aapl:1_min"
    assert result == expected_key


def test_create_ts(ohlcv_ts, mock_shared_redis_client, sample_extend_contract_request):
    """Test the create_ts method."""
    ohlcv_ts.create_ts(sample_extend_contract_request)
    expected_key = "candle_ts:stk:usd:aapl:1_min"
    mock_shared_redis_client.ts.return_value.create.assert_called_once_with(expected_key)
    assert (
        sample_extend_contract_request.sec_type.value,
        sample_extend_contract_request.currency.value,
        sample_extend_contract_request.symbol,
        sample_extend_contract_request.bar_size.value,
    ) in ohlcv_ts.created_ts_cache

    mock_shared_redis_client.ts.return_value.create.reset_mock()
    ohlcv_ts.create_ts(sample_extend_contract_request)
    mock_shared_redis_client.ts.return_value.create.assert_not_called()


def test_add_data(ohlcv_ts, mock_shared_redis_client, sample_extend_contract_request, sample_ohlcv_data):
    """Test the add_data method."""
    mock_shared_redis_client.ts.return_value.get.return_value = None

    ohlcv_ts.add_data(sample_ohlcv_data, sample_extend_contract_request)

    expected_key = "candle_ts:stk:usd:aapl:1_min"
    expected_value = (
        f"{sample_ohlcv_data.open},{sample_ohlcv_data.high},"  # noqa E231
        f"{sample_ohlcv_data.low},{sample_ohlcv_data.close},"  # noqa E231
        f"{sample_ohlcv_data.volume},{sample_ohlcv_data.wap},"  # noqa E231
        f"{sample_ohlcv_data.barcount}"  # noqa E231
    )
    mock_shared_redis_client.ts.return_value.add.assert_called_once_with(
        expected_key, sample_ohlcv_data.timestamp, expected_value
    )

    mock_shared_redis_client.ts.return_value.get.return_value = ("existing_data",)
    with pytest.raises(TimeSeriesModelException, match="Data already exists for timestamp"):
        ohlcv_ts.add_data(sample_ohlcv_data, sample_extend_contract_request)

    mock_shared_redis_client.ts.return_value.get.return_value = None
    mock_shared_redis_client.ts.return_value.add.side_effect = Exception("Test error")
    with pytest.raises(TimeSeriesModelException, match="Failed to add candle"):
        ohlcv_ts.add_data(sample_ohlcv_data, sample_extend_contract_request)


def test_get_data(ohlcv_ts, mock_shared_redis_client, sample_candle_data, sample_extend_contract_request):
    """Test the get_data method."""
    candle_request = CandleRequest(
        extend_contract_request=sample_extend_contract_request, from_time=1609459200000, to_time=1609459260000
    )

    mock_shared_redis_client.ts.return_value.range.return_value = sample_candle_data

    result = ohlcv_ts.get_data(candle_request)

    assert len(result) == 2
    assert isinstance(result[0], OhlcvCandleData)
    assert result[0].timestamp == 1609459200000
    assert result[0].open == 100.0
    assert result[0].high == 105.0
    assert result[0].low == 98.0
    assert result[0].close == 103.0
    assert result[0].volume == 1000
    assert result[0].wap == 102.5
    assert result[0].barcount == 50

    mock_shared_redis_client.ts.return_value.range.return_value = []
    result = ohlcv_ts.get_data(candle_request)
    assert result == []

    mock_shared_redis_client.ts.return_value.range.side_effect = Exception("Test error")
    with pytest.raises(TimeSeriesModelException, match="Failed to get candles"):
        ohlcv_ts.get_data(candle_request)


def test_get_latest_data(ohlcv_ts, mock_shared_redis_client, sample_extend_contract_request):
    """Test the get_latest_data method."""
    mock_shared_redis_client.ts.return_value.get.return_value = (1609459200000, "100.0,105.0,98.0,103.0,1000,102.5,50")

    result = ohlcv_ts.get_latest_data(sample_extend_contract_request)

    assert isinstance(result, OhlcvCandleData)
    assert result.timestamp == 1609459200000
    assert result.open == 100.0
    assert result.high == 105.0
    assert result.low == 98.0
    assert result.close == 103.0
    assert result.volume == 1000
    assert result.wap == 102.5
    assert result.barcount == 50

    mock_shared_redis_client.ts.return_value.get.return_value = None
    result = ohlcv_ts.get_latest_data(sample_extend_contract_request)
    assert result is None

    mock_shared_redis_client.ts.return_value.get.return_value = (1609459200000, "100.0,105.0,98.0,103.0,1000,-1,-1")
    result = ohlcv_ts.get_latest_data(sample_extend_contract_request)
    assert result.wap is None
    assert result.barcount is None

    mock_shared_redis_client.ts.return_value.get.side_effect = Exception("Test error")
    with pytest.raises(TimeSeriesModelException, match="Failed to get latest candle"):
        ohlcv_ts.get_latest_data(sample_extend_contract_request)


def test_update_metadata(ohlcv_ts, mock_shared_redis_client, caplog, sample_extend_contract_request):
    """Test the update_metadata method."""
    metadata_key = (
        f"{sample_extend_contract_request.sec_type.value}:"  # noqa E231
        f"{sample_extend_contract_request.currency.value}:"  # noqa E231
        f"{sample_extend_contract_request.symbol}"  # noqa E231
    )

    mock_shared_redis_client.hget.return_value = None
    ohlcv_ts._update_metadata(  # pylint: disable=protected-access
        sample_extend_contract_request.sec_type.value,
        sample_extend_contract_request.currency.value,
        sample_extend_contract_request.symbol,
        sample_extend_contract_request.bar_size.value,
    )
    mock_shared_redis_client.hset.assert_called_once_with(ohlcv_ts.metadata_key, metadata_key, "1_min")

    mock_shared_redis_client.hget.return_value = "1_min"
    ohlcv_ts._update_metadata(  # pylint: disable=protected-access
        sample_extend_contract_request.sec_type.value,
        sample_extend_contract_request.currency.value,
        sample_extend_contract_request.symbol,
        "5 min",
    )

    mock_shared_redis_client.hset.assert_called_with(
        ohlcv_ts.metadata_key, metadata_key, mock_shared_redis_client.hset.call_args[0][2]
    )

    assert set(mock_shared_redis_client.hset.call_args[0][2].split(",")) == {"1_min", "5_min"}

    mock_shared_redis_client.hget.side_effect = Exception("Test error")
    with pytest.raises(OhlcvCandleException) as excinfo:
        ohlcv_ts._update_metadata(  # pylint: disable=protected-access
            sample_extend_contract_request.sec_type.value,
            sample_extend_contract_request.currency.value,
            sample_extend_contract_request.symbol,
            sample_extend_contract_request.bar_size.value,
        )
    assert "Failed to update metadata for key STK:USD:AAPL: Test error" in str(excinfo.value)
    assert "Failed to update metadata for key STK:USD:AAPL: Test error" in caplog.text


def test_get_symbols(ohlcv_ts, mock_shared_redis_client):
    """Test the get_symbols method."""
    mock_metadata = {"STK:USD:AAPL": "1 min,5 min", "STK:USD:GOOGL": "1 min", "STK:EUR:BMW": "1 hour"}
    mock_shared_redis_client.hgetall.return_value = mock_metadata

    symbols = ohlcv_ts.get_symbols()
    assert set(symbols) == {"AAPL", "GOOGL", "BMW"}


def test_get_symbols_and_bar_sizes(ohlcv_ts, mock_shared_redis_client):
    """Test the get_symbols_and_bar_sizes method."""
    mock_metadata = {
        "STK:USD:AAPL": f"{BarSize.ONE_MINUTE.value},{BarSize.FIVE_MINUTES.value}",  # noqa E231
        "STK:USD:GOOGL": f"{BarSize.ONE_MINUTE.value}",  # noqa E231
        "STK:EUR:BMW": f"{BarSize.ONE_HOUR.value}",  # noqa E231
    }
    mock_shared_redis_client.hgetall.return_value = mock_metadata

    ohlcv_ts._unsanitize_bar_size = (  # pylint: disable=protected-access
        lambda x: x
    )  # No need to unsanitize, using enum values directly
    ohlcv_ts._get_min_timestamp = MagicMock(return_value=1609459200000)  # pylint: disable=protected-access

    result = ohlcv_ts.get_symbols_and_bar_sizes()

    expected_result = {
        "AAPL": [(BarSize.ONE_MINUTE.value, 1609459200000), (BarSize.FIVE_MINUTES.value, 1609459200000)],
        "GOOGL": [(BarSize.ONE_MINUTE.value, 1609459200000)],
    }
    assert result == expected_result

    # Test with different sec_type and currency
    result = ohlcv_ts.get_symbols_and_bar_sizes(sec_type="STK", currency="EUR")

    expected_result = {"BMW": [(BarSize.ONE_HOUR.value, 1609459200000)]}
    assert result == expected_result
