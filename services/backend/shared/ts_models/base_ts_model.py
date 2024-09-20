import logging
import re
from abc import (
    ABC,
    abstractmethod,
)
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

from shared.redis_interfacce import SharedRedisClient

T = TypeVar("T")


class TimeSeriesModelException(Exception):
    """Time Series Model Exception."""


class BaseTimeSeriesModel(ABC):
    """Base Time Series Model."""

    def __init__(self, prefix: str, debug: bool = False, expire: Optional[int] = None):
        self.redis_client = SharedRedisClient.get_instance()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.expire = expire
        self.prefix = prefix
        self.metadata_key = f"{self.__class__.__name__.lower()}_timeseries_metadata"
        self.ts_key_cache: Dict[Tuple[str, ...], str] = {}
        self.created_ts_cache: Set[Tuple[str, ...]] = set()
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def _sanitize_key(self, value: Any) -> str:
        """Sanitize key value."""
        if not value:
            raise ValueError("Key value cannot be empty.")

        if isinstance(value, Enum):
            value = value.value

        value = str(value)
        sanitized = value.lower().replace(" ", "_")
        sanitized = re.sub(r"[^\w-]", "", sanitized)

        return sanitized

    def get_key(self, *args: Any) -> str:
        """Get key for time series."""
        key = tuple(str(arg) for arg in args)
        if key not in self.ts_key_cache:
            sanitized_args = [self._sanitize_key(arg) for arg in args]
            self.ts_key_cache[key] = f"{self.prefix}:{':'.join(sanitized_args)}"  # noqa E231
        return self.ts_key_cache[key]

    def create_ts(self, *args: Any) -> None:
        """Create time series."""
        key = self.get_key(*args)
        cache_key = tuple(str(arg) for arg in args)
        if cache_key in self.created_ts_cache:
            return

        try:
            self.redis_client.ts().create(key)
            if self.expire:
                self.redis_client.expire(key, self.expire)
            self.logger.debug("Created time series for key: %s", key)
            self.created_ts_cache.add(cache_key)
            self._update_metadata(*args)
        except Exception as e:
            raise TimeSeriesModelException(f"Failed to create time series for key {key}: {str(e)}")

    @abstractmethod
    def add_data(self, data: T, **kwargs: Any) -> None:
        """Add data to time series."""

    @abstractmethod
    def get_data(self, *args: Any) -> List[T]:
        """Get data from time series."""

    def delete_data(self, *args: Any) -> None:
        """Delete data from time series."""
        key = self.get_key(*args)
        cache_key = tuple(str(arg) for arg in args)
        try:
            self.redis_client.delete(key)
            self.logger.debug("Deleted time series for key: %s", key)
            self.created_ts_cache.discard(cache_key)
            self.ts_key_cache.pop(cache_key, None)
        except Exception as e:
            self.logger.error("Failed to delete time series for key %s:,%s,", key, str(e))
            raise TimeSeriesModelException(f"Failed to delete time series for key {key}: {str(e)}")

    @abstractmethod
    def get_latest_data(self, *args: Any) -> Optional[T]:
        """Get latest data from time series."""

    def _update_metadata(self, *args: Any) -> None:
        """Update metadata."""
        metadata_key = ":".join(str(arg) for arg in args)
        try:
            self.redis_client.hset(self.metadata_key, metadata_key, "")
        except TimeSeriesModelException as e:
            self.logger.error("Failed to update metadata for key %s: %s", metadata_key, str(e))

    def clear_cache(self) -> None:
        """Clear cache."""
        self.ts_key_cache.clear()
        self.created_ts_cache.clear()
