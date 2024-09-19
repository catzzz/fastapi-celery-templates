"""Test cases for the OhlcvCandleTS class."""

import logging
from unittest.mock import MagicMock

import pytest
from apis.models.candle_ts import (
    OHLCV_FIELDS,
    DataExistsError,
    OhlcvCandleData,
    OhlcvCandleTS,
    TimestampError,
)
from apis.schemas.candle_request import CandleRequest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def ohlcv_ts(mock_shared_redis_client):  # pylint: disable=unused-argument
    """Return an instance of OhlcvCandleTS."""
    return OhlcvCandleTS(debug=True)


def test_create_ts(ohlcv_ts, mock_shared_redis_client):
    """Test create_ts method."""
    ohlcv_ts.create_ts("STK", "AAPL", "1 min")

    # Assert that the time series was created
    assert mock_shared_redis_client.ts().create.called

    # Check if the base key was created
    mock_shared_redis_client.ts().create.assert_any_call("ts:STK:AAPL:1_min")

    # Assert that metadata was updated
    mock_shared_redis_client.hset.assert_called_with("ohlcv_timeseries_metadata", "STK:AAPL", "1 min")


def test_add_candle(ohlcv_ts, mock_shared_redis_client):
    """Test add_candle method."""
    candle_data = {
        "timestamp": 1633027200000,
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
        "volume": 1000000,
        "wap": 100.2,
        "barcount": 100,
    }

    # Reset the mock before calling add_candle
    mock_shared_redis_client.reset_mock()

    # Ensure that ts().get returns None to simulate that the data doesn't exist
    mock_shared_redis_client.ts().get.return_value = None

    ohlcv_ts.add_candle("STK", "AAPL", "1 min", candle_data)

    # Assert that ts().add was called
    assert mock_shared_redis_client.ts().add.called

    # Check if add was called for each field
    for field in OHLCV_FIELDS:
        mock_shared_redis_client.ts().add.assert_any_call(
            f"ts:STK:AAPL:1_min:{field}", 1633027200000, candle_data[field]  # noqa E231
        )

    # Print debug information
    print("Mock calls:")
    print(mock_shared_redis_client.mock_calls)
    print("\nTS add calls:")
    print(mock_shared_redis_client.ts().add.mock_calls)


def test_get_candles(ohlcv_ts, mock_shared_redis_client, caplog):
    """Test get_candles method."""
    caplog.set_level(logging.DEBUG)

    mock_data = {
        "open": [(1633027200000, 100.0), (1633027260000, 101.0)],
        "high": [(1633027200000, 102.0), (1633027260000, 103.0)],
        "low": [(1633027200000, 99.0), (1633027260000, 100.0)],
        "close": [(1633027200000, 101.0), (1633027260000, 102.0)],
        "volume": [(1633027200000, 1000), (1633027260000, 1100)],
        "wap": [(1633027200000, 100.5), (1633027260000, 101.5)],
        "barcount": [(1633027200000, 100), (1633027260000, 110)],
    }

    # Mock the pipeline behavior
    mock_pipeline = MagicMock()
    mock_pipeline.ts().range.side_effect = lambda key, *args: mock_data[key.split(":")[-1]]
    mock_pipeline.execute.return_value = [mock_data[field] for field in OHLCV_FIELDS]
    mock_shared_redis_client.pipeline.return_value = mock_pipeline

    print("Debug: Mock pipeline execute return value:")
    print(mock_pipeline.execute.return_value)

    candle_request = CandleRequest(
        sec_type="STK", symbol="AAPL", bar_size="1 min", from_time=1633027200000, to_time=1633027260000
    )

    candles = ohlcv_ts.get_candles(candle_request)

    print("Debug: Returned candles:")
    print(candles)

    print("Debug: Captured logs:")
    print(caplog.text)

    assert len(candles) == 2, f"Expected 2 candles, but got {len(candles)}"
    assert isinstance(candles[0], OhlcvCandleData), "Expected OhlcvCandleData object"
    assert candles[0].timestamp == 1633027200000, f"Expected timestamp 1633027200000, but got {candles[0].timestamp}"
    assert candles[0].open == 100.0, f"Expected open 100.0, but got {candles[0].open}"
    assert candles[1].timestamp == 1633027260000, f"Expected timestamp 1633027260000, but got {candles[1].timestamp}"
    assert candles[1].open == 101.0, f"Expected open 101.0, but got {candles[1].open}"

    # Print mock calls
    print("Debug: Mock calls:")
    print(mock_shared_redis_client.mock_calls)


def test_delete_candles(ohlcv_ts, mock_shared_redis_client):
    """Test delete_candles method."""
    candle_request = CandleRequest(
        sec_type="STK", symbol="AAPL", bar_size="1 min", from_time=1633027200000, to_time=1633027260000
    )

    # Mock the pipeline behavior
    mock_pipeline = MagicMock()
    mock_shared_redis_client.pipeline.return_value = mock_pipeline

    ohlcv_ts.delete_candles(candle_request)

    # Assert that pipeline().ts().del_range was called for each field
    for field in OHLCV_FIELDS:
        mock_pipeline.ts().del_range.assert_any_call(
            f"ts:STK:AAPL:1_min:{field}", 1633027200000, 1633027260000  # noqa E231
        )  # noqa E231

    # Assert that pipeline.execute() was called
    mock_pipeline.execute.assert_called_once()

    # Print debug information
    print("Mock calls:")
    print(mock_shared_redis_client.mock_calls)
    print("\nPipeline mock calls:")
    print(mock_pipeline.mock_calls)


def test_get_latest_candle(ohlcv_ts, mock_shared_redis_client):
    """Test get_latest_candle method."""
    mock_data = {
        "open": (1633027200000, 100.0),
        "high": (1633027200000, 102.0),
        "low": (1633027200000, 99.0),
        "close": (1633027200000, 101.0),
        "volume": (1633027200000, 1000),
        "wap": (1633027200000, 100.5),
        "barcount": (1633027200000, 100),
    }

    mock_shared_redis_client.ts().get.side_effect = lambda key: mock_data[key.split(":")[-1]]

    latest_candle = ohlcv_ts.get_latest_candle("STK", "AAPL", "1 min")

    assert isinstance(latest_candle, OhlcvCandleData), "Expected OhlcvCandleData object"
    assert latest_candle.timestamp == 1633027200000
    assert latest_candle.open == 100.0
    assert latest_candle.high == 102.0
    assert latest_candle.low == 99.0
    assert latest_candle.close == 101.0
    assert latest_candle.volume == 1000
    assert latest_candle.wap == 100.5
    assert latest_candle.barcount == 100


def test_get_candle_count(ohlcv_ts, mock_shared_redis_client):
    """Test get_candle_count method."""

    class MockInfo:
        """Mock class for Redis time series info."""

        total_samples = 100

    mock_shared_redis_client.ts().info.return_value = MockInfo()

    count = ohlcv_ts.get_candle_count("STK", "AAPL", "1 min")

    assert count == 100
    mock_shared_redis_client.ts().info.assert_called_with("ts:STK:AAPL:1_min:open")


# Additional tests


def test_add_candle_timestamp_error(ohlcv_ts, caplog):
    """Test add_candle method with missing timestamp."""
    caplog.set_level(logging.DEBUG)

    with pytest.raises(TimestampError) as exc_info:
        ohlcv_ts.add_candle("STK", "AAPL", "1 min", {"Open": 100.0})  # Missing timestamp

    print("Captured logs:")
    print(caplog.text)

    assert str(exc_info.value) == "Timestamp is required in candle_data"


def test_add_candle_data_exists_error(ohlcv_ts, mock_shared_redis_client, caplog):
    """Test add_candle method when data already exists."""
    caplog.set_level(logging.DEBUG)

    mock_shared_redis_client.ts().get.return_value = (1633027200000, 100.0)

    with pytest.raises(DataExistsError) as exc_info:
        ohlcv_ts.add_candle("STK", "AAPL", "1 min", {"timestamp": 1633027200000, "Open": 100.0})

    print("Captured logs:")
    print(caplog.text)

    assert str(exc_info.value) == "Data already exists for timestamp 1633027200000"


# Add this helper function to your test file
def print_mock_calls(mock_obj):
    """Print the calls made to a mock object."""
    print("Mock calls:")
    for call in mock_obj.mock_calls:
        print(f"  {call}")


def test_get_symbols(ohlcv_ts, mock_shared_redis_client):
    """Test get_symbols method."""
    mock_shared_redis_client.hgetall.return_value = {"STK:AAPL": "1 min", "STK:GOOGL": "5 min"}

    symbols = ohlcv_ts.get_symbols()

    assert set(symbols) == {"AAPL", "GOOGL"}


def test_get_symbols_and_bar_sizes(ohlcv_ts, mock_shared_redis_client):
    """Test get_symbols_and_bar_sizes method."""
    mock_shared_redis_client.hgetall.return_value = {"STK:AAPL": "1_min,5_min", "STK:GOOGL": "1_min"}
    mock_shared_redis_client.ts().range.return_value = [(1633027200000, 100.0)]

    result = ohlcv_ts.get_symbols_and_bar_sizes()

    assert "AAPL" in result
    assert "GOOGL" in result
    assert ("1 min", 1633027200000) in result["AAPL"]
    assert ("5 min", 1633027200000) in result["AAPL"]
    assert ("1 min", 1633027200000) in result["GOOGL"]
