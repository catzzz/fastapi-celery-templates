"""Test base timeseries ."""

import logging
from enum import Enum
from typing import (
    Any,
    List,
    Optional,
)
from unittest.mock import patch

import pytest
from shared.ts_models.base_ts_model import (
    BaseTimeSeriesModel,
    TimeSeriesModelException,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestTimeSeriesModel(BaseTimeSeriesModel):
    """Test Time Series Model."""

    def add_data(self, data: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        """Add data to time series."""

    def get_data(self, *args: Any) -> List[Any]:  # pylint: disable=unused-argument
        """Get data from time series."""

    def get_latest_data(self, *args: Any) -> Optional[Any]:  # pylint: disable=unused-argument
        """Get latest data from time series."""


@pytest.fixture
def base_ts_model():
    """Return an instance of TestTimeSeriesModel."""
    return TestTimeSeriesModel(prefix="test", debug=True)


class TestEnum(Enum):
    """Test Enum."""

    VALUE1 = "value1"
    VALUE2 = "value2"


def test_sanitize_key(base_ts_model):
    """Test the _sanitize_key method."""
    assert base_ts_model._sanitize_key("Test Value") == "test_value"  # pylint: disable=protected-access
    assert base_ts_model._sanitize_key("Test-Value") == "test-value"  # pylint: disable=protected-access
    assert base_ts_model._sanitize_key("Test@Value") == "testvalue"  # pylint: disable=protected-access
    assert base_ts_model._sanitize_key("123Test") == "123test"  # pylint: disable=protected-access
    assert base_ts_model._sanitize_key(TestEnum.VALUE1) == "value1"  # pylint: disable=protected-access

    with pytest.raises(ValueError):
        base_ts_model._sanitize_key("")  # pylint: disable=protected-access


def test_get_key(base_ts_model):
    """Test the get_key method."""
    assert (
        base_ts_model.get_key(
            "STK",
            "USD",
            "AAPL",
            "1 min",
        )
        == "test:stk:usd:aapl:1_min"
    )
    assert (
        base_ts_model.get_key(
            "STK",
            "USD",
            "GOOGL",
            "5 min",
        )
        == "test:stk:usd:googl:5_min"
    )
    assert (
        base_ts_model.get_key(
            "STK",
            "USD",
            "MSFT",
            "1 hour",
        )
        == "test:stk:usd:msft:1_hour"
    )

    # Test caching
    key = base_ts_model.get_key(
        "STK",
        "USD",
        "AAPL",
        "1 min",
    )
    assert (
        "STK",
        "USD",
        "AAPL",
        "1 min",
    ) in base_ts_model.ts_key_cache
    assert (
        base_ts_model.ts_key_cache[
            (
                "STK",
                "USD",
                "AAPL",
                "1 min",
            )
        ]
        == key
    )


def test_create_ts(base_ts_model):
    """Test the create_ts method."""
    with patch.object(base_ts_model.redis_client, "ts") as mock_ts:
        base_ts_model.create_ts("Test", "Value")
        mock_ts.return_value.create.assert_called_once_with("test:test:value")

        # Test caching
        assert ("Test", "Value") in base_ts_model.created_ts_cache

        # Test creating the same TS again
        base_ts_model.create_ts("Test", "Value")
        mock_ts.return_value.create.assert_called_once()  # Should not be called again

    # Test exception handling
    with patch.object(base_ts_model.redis_client, "ts") as mock_ts:
        mock_ts.return_value.create.side_effect = Exception("Test error")
        with pytest.raises(TimeSeriesModelException):
            base_ts_model.create_ts("Error", "Test")


def test_delete_data(base_ts_model):
    """Test the delete_data method."""
    # First, add some data to the cache
    base_ts_model.ts_key_cache[("Test", "Value")] = "test:test:value"
    base_ts_model.created_ts_cache.add(("Test", "Value"))

    with patch.object(base_ts_model.redis_client, "delete") as mock_delete:
        base_ts_model.delete_data("Test", "Value")
        mock_delete.assert_called_once_with("test:test:value")

        # Check that the caches were updated
        assert ("Test", "Value") not in base_ts_model.created_ts_cache
        assert ("Test", "Value") not in base_ts_model.ts_key_cache

    # Test exception handling
    with patch.object(base_ts_model.redis_client, "delete") as mock_delete:
        mock_delete.side_effect = Exception("Test error")
        with pytest.raises(TimeSeriesModelException):
            base_ts_model.delete_data("Error", "Test")


def test_update_metadata(base_ts_model):
    """Test the _update_metadata method."""
    with patch.object(base_ts_model.redis_client, "hset") as mock_hset:
        base_ts_model._update_metadata("Test", "Value")  # pylint: disable=protected-access
        mock_hset.assert_called_once_with(base_ts_model.metadata_key, "Test:Value", "")

    # Test exception handling
    with patch.object(base_ts_model.redis_client, "hset") as mock_hset:
        mock_hset.side_effect = TimeSeriesModelException("Test error")
        base_ts_model._update_metadata("Error", "Test")  # pylint: disable=protected-access
        # Check that the error was logged (you might need to mock the logger and check its calls)


def test_clear_cache(base_ts_model):
    """Test the clear_cache method."""
    # Add some data to the caches
    base_ts_model.ts_key_cache[("Test", "Value")] = "test:test:value"  # noqa E231
    base_ts_model.created_ts_cache.add(("Test", "Value"))

    base_ts_model.clear_cache()

    assert len(base_ts_model.ts_key_cache) == 0
    assert len(base_ts_model.created_ts_cache) == 0
