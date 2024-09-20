from datetime import (
    datetime,
    timezone,
)
from unittest.mock import MagicMock

import pytest
from shared.enums.status import Status
from shared.ts_models.task_status_ts import (
    TaskStatusData,
    TaskStatusTs,
    TimeSeriesModelException,
)


@pytest.fixture
def task_status_ts(mock_shared_redis_client):  # pylint: disable=unused-argument
    """Return an instance of TaskStatusTs."""
    return TaskStatusTs(debug=True)


@pytest.fixture
def mock_redis_client(monkeypatch):
    """Mock SharedRedisClient.get_instance method."""
    mock_client = MagicMock()
    monkeypatch.setattr("apis.redis_interfacce.SharedRedisClient.get_instance", lambda: mock_client)
    return mock_client


def test_add_data(task_status_ts, mock_shared_redis_client):
    """Test add_data method of TaskStatusTs class."""
    # Prepare test data
    test_data = TaskStatusData(
        timestamp=int(datetime.now(timezone.utc).timestamp() * 1000),
        status=Status.PENDING,
        user_id=123,
        payload_id=456,
        payload_table="test_table",
        worker_id="test_worker",
    )

    # Test successful data addition
    task_status_ts.add_data(test_data)

    # Assert that ts().add was called with correct arguments
    mock_shared_redis_client.ts.return_value.add.assert_called_once_with(
        "task_status:test_table:456",  # noqa E231
        test_data.timestamp,
        1,
        labels={
            "status": "pending",
            "user_id": "123",
            "worker_id": "test_worker",
        },
    )

    # Test error handling
    mock_shared_redis_client.ts.return_value.add.side_effect = Exception("Test error")
    with pytest.raises(TimeSeriesModelException):
        task_status_ts.add_data(test_data)


def test_get_data(task_status_ts, mock_shared_redis_client):
    """Test get_data method of TaskStatusTs class."""
    # Prepare test data
    payload_table = "test_table"
    payload_id = 456
    start_time = 0
    end_time = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Mock Redis response
    mock_shared_redis_client.ts.return_value.range.return_value = [
        (1625097600000, 1, {"status": "pending", "user_id": "123", "worker_id": "test_worker"}),
        (1625097601000, 1, {"status": "in_progress", "user_id": "123", "worker_id": "test_worker"}),
        (1625097602000, 1, {"status": "completed", "user_id": "123", "worker_id": "test_worker"}),
    ]

    # Test successful data retrieval
    result = task_status_ts.get_data(payload_table, payload_id, start_time, end_time)

    # Assert that ts().range was called with correct arguments
    mock_shared_redis_client.ts.return_value.range.assert_called_once_with(
        "task_status:test_table:456", start_time, end_time, with_labels=True  # noqa E231
    )

    # Check the returned data
    assert len(result) == 3
    assert all(isinstance(item, TaskStatusData) for item in result)
    assert [item.status for item in result] == [Status.PENDING, Status.IN_PROGRESS, Status.COMPLETED]

    # Test error handling
    mock_shared_redis_client.ts.return_value.range.side_effect = TimeSeriesModelException("Test error")
    result = task_status_ts.get_data(payload_table, payload_id, start_time, end_time)
    assert result == []
