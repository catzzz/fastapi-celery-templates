from typing import (
    Any,
    List,
    Optional,
    override,
)

from pydantic import (
    BaseModel,
    Field,
)
from shared.enums.status import Status

from .base_ts_model import (
    BaseTimeSeriesModel,
    TimeSeriesModelException,
)


class TaskStatusData(BaseModel):
    """Task Status TimeSeries Data model."""

    timestamp: int
    status: Status
    user_id: int
    payload_id: int
    payload_table: str
    worker_id: Optional[str] = Field(None, description="Additional worker id to identify the worker.")


class TaskStatusTs(BaseTimeSeriesModel):
    """Task Status Time Series model."""

    def __init__(self, debug: bool = False, expire: Optional[int] = 3600):
        super().__init__(prefix="task_status", debug=debug, expire=expire)

    @override
    # pylint: disable=arguments-differ
    def get_key(self, payload_table: str, payload_id: int) -> str:
        """Get key for time series."""
        return super().get_key(payload_table, str(payload_id))

    @override
    # pylint: disable=arguments-differ
    def create_ts(self, payload_table: str, payload_id: int) -> None:
        """Create time series."""
        super().create_ts(payload_table, str(payload_id))

    @override
    # pylint: disable=arguments-differ
    def add_data(self, data: TaskStatusData, **kwargs: Any) -> None:
        """Add data to time series."""
        key = self.get_key(data.payload_table, data.payload_id)
        try:
            self.create_ts(data.payload_table, data.payload_id)
            self.redis_client.ts().add(
                key,
                data.timestamp,
                1,
                labels={
                    "status": self._sanitize_key(data.status.value),
                    "user_id": str(data.user_id),
                    "worker_id": data.worker_id or "unknown",
                },
            )
            self.logger.debug("Added data to time series for key: %s", key)
        except Exception as e:
            raise TimeSeriesModelException(f"Failed to add data to time series for key {key}: {str(e)}")

    @override
    # pylint: disable=arguments-differ
    def get_data(
        self, payload_table: str, payload_id: int, start_time: int = "-", end_time: int = "+"
    ) -> List[TaskStatusData]:
        """Get data from time series."""
        key = self.get_key(payload_table, payload_id)
        try:
            result = self.redis_client.ts().range(key, start_time, end_time, with_labels=True)
            return [
                TaskStatusData(
                    timestamp=entry[0],
                    status=Status(entry[2]["status"]),
                    user_id=int(entry[2]["user_id"]),
                    payload_id=payload_id,
                    payload_table=payload_table,
                    worker_id=entry[2].get("worker_id"),
                )
                for entry in result
            ]
        except TimeSeriesModelException as e:
            self.logger.error("Failed to get data from time series for key %s: %s", key, str(e))
            return []

    @override
    # pylint: disable=arguments-differ
    def get_latest_data(self, payload_table: str, payload_id: int) -> Optional[TaskStatusData]:
        """Get latest data from time series."""
        key = self.get_key(payload_table, payload_id)
        try:
            result = self.redis_client.ts().get(key)
            return [
                TaskStatusData(
                    timestamp=entry[0],
                    status=Status(entry[2]["status"]),
                    user_id=int(entry[2]["user_id"]),
                    payload_id=payload_id,
                    payload_table=payload_table,
                    worker_id=entry[2].get("worker_id"),
                )
                for entry in result
            ]
        except TimeSeriesModelException as e:
            self.logger.error("Failed to get latest data from time series for key %s: %s", key, str(e))
            return None
