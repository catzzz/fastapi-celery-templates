"""OhlcvCandleTS class to interact with RedisTimeSeries for OHLCV data."""

import logging
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

import pytz
from apis.redis_interfacce import SharedRedisClient
from apis.schemas.candle_request import CandleRequest
from pydantic import BaseModel
from redis.exceptions import ResponseError


class BarSizeMinTimestamp(BaseModel):
    """Bar size and minimum timestamp."""

    bar_size: str
    min_timestamp: int


class TimeSeriesSymbolsBarSizeKey(BaseModel):
    """Time series symbols and bar sizes key."""

    symbol: str
    bar_size_min_timestamps: List[BarSizeMinTimestamp]


OHLCV_FIELDS = ["open", "high", "low", "close", "volume", "wap", "barcount"]


class OhlcvCandleData(BaseModel):
    """OHLCV Candle data model."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int
    wap: float
    barcount: int


class OhlcvError(Exception):
    """Base exception for OHLCV errors."""


class TimestampError(OhlcvError):
    """Exception for timestamp-related errors."""


class DataExistsError(OhlcvError):
    """Exception for when data already exists."""


class OhlcvCandleTS:
    """OHLCV Candle Time Series class."""

    def __init__(self, debug: bool = False):
        self.redis_client = SharedRedisClient.get_instance()
        self.metadata_key = "ohlcv_timeseries_metadata"
        self.ts_key_cache: Dict[Tuple[str, str, str], str] = {}
        self.created_ts_cache: Set[Tuple[str, str, str]] = set()
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def _sanitize_key(self, value: str) -> str:
        """Sanitize key value."""
        return value.replace(" ", "_")

    def _unsanitize_bar_size(self, value: str) -> str:
        """Unsanitize bar size value."""
        return value.replace("_", " ")

    def _generate_key(self, sec_type: str, symbol: str, bar_size: str, field: str = "") -> str:
        """Generate time series key."""
        key = (sec_type, symbol, bar_size)
        if key not in self.ts_key_cache:
            self.ts_key_cache[
                key
            ] = f"ts:{self._sanitize_key(sec_type)}:{self._sanitize_key(symbol)}:{self._sanitize_key(bar_size)}"  # noqa E231
        base_key = self.ts_key_cache[key]
        return f"{base_key}:{field}" if field else base_key  # noqa E231

    def create_ts(self, sec_type: str, symbol: str, bar_size: str) -> None:
        """Create time series."""
        key = (sec_type, symbol, bar_size)
        if key in self.created_ts_cache:
            return

        try:
            base_key = self._generate_key(sec_type, symbol, bar_size)
            pipeline = self.redis_client.pipeline()
            pipeline.ts().create(base_key)
            for field in OHLCV_FIELDS:
                pipeline.ts().create(f"{base_key}:{field}")  # noqa E231
            pipeline.execute()

            self._update_metadata(sec_type, symbol, bar_size)
            self.created_ts_cache.add(key)
        except ResponseError as e:
            if "already exists" in str(e):
                self.created_ts_cache.add(key)
            else:
                self.logger.error("Error creating time series: %s", e)
                raise OhlcvError(f"Failed to create time series: {e}")

    def _update_metadata(self, sec_type: str, symbol: str, bar_size: str) -> None:
        """Update metadata."""
        metadata_key = f"{sec_type}:{symbol}"  # noqa E231
        current_bar_sizes = self.redis_client.hget(self.metadata_key, metadata_key)
        if current_bar_sizes:
            bar_sizes = set(current_bar_sizes.split(","))
            bar_sizes.add(bar_size)
            self.redis_client.hset(self.metadata_key, metadata_key, ",".join(bar_sizes))
        else:
            self.redis_client.hset(self.metadata_key, metadata_key, bar_size)

    def add_candle(self, sec_type: str, symbol: str, bar_size: str, candle_data: Dict[str, Any]) -> None:
        """Add candle data."""
        try:
            self.logger.debug("Adding candle: %s %s %s %s", sec_type, symbol, bar_size, candle_data)

            if "timestamp" not in candle_data or candle_data["timestamp"] == 0:
                self.logger.warning("Timestamp is required in candle_data")
                raise TimestampError("Timestamp is required in candle_data")

            timestamp = int(candle_data["timestamp"])

            self.create_ts(sec_type, symbol, bar_size)
            base_key = self._generate_key(sec_type, symbol, bar_size)

            # Check if data already exists
            existing_data = self.redis_client.ts().get(f"{base_key}:open", timestamp)  # noqa E231
            if existing_data:
                self.logger.warning("Data already exists for timestamp %s", timestamp)
                raise DataExistsError(f"Data already exists for timestamp {timestamp}")

            pipeline = self.redis_client.pipeline()
            for field in OHLCV_FIELDS:
                value = candle_data.get(field.lower())
                if value is not None:
                    value = float(value) if field in ["open", "high", "low", "close", "wap"] else int(value)
                    pipeline.ts().add(f"{base_key}:{field}", timestamp, value)  # noqa E231
            pipeline.execute()
            self.logger.debug("Successfully added candle for timestamp %s", timestamp)

        except (TimestampError, DataExistsError) as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error("Failed to add candle: %s", str(e), exc_info=True)
            raise OhlcvError(f"Failed to add candle: {e}")

    def get_candles(self, candle_request: CandleRequest) -> List[OhlcvCandleData]:
        """Get candles."""
        try:
            base_key = self._generate_key(candle_request.sec_type, candle_request.symbol, candle_request.bar_size)
            self.logger.debug("Generated base key: %s", base_key)

            pipeline = self.redis_client.pipeline()
            for field in OHLCV_FIELDS:
                pipeline.ts().range(
                    f"{base_key}:{field}", candle_request.from_time, candle_request.to_time  # noqa E231
                )  # noqa E231

            results = pipeline.execute()
            self.logger.debug("Pipeline execution results: %s", results)

            if results is None or not any(results):
                self.logger.info("No data found for %s", candle_request)
                return []

            data = dict(zip(OHLCV_FIELDS, results, strict=True))
            self.logger.debug("Data after zipping: %s", data)

            min_length = min(len(field_data) for field_data in data.values() if field_data)
            self.logger.debug("Minimum length of data: %s", min_length)

            candles = [
                OhlcvCandleData(
                    timestamp=data["open"][i][0] if data["open"] else 0,
                    **{
                        field: data[field][i][1] if data[field] and i < len(data[field]) else 0
                        for field in OHLCV_FIELDS
                    },
                )
                for i in range(min_length)
            ]
            self.logger.debug("Generated candles: %s", candles)

            return candles
        except Exception as e:
            self.logger.error("Error getting candles: %s ", str(e), exc_info=True)
            raise OhlcvError(f"Failed to get candles: {e}")

    def delete_candles(self, candle_request: CandleRequest) -> None:
        """Delete candles."""
        try:
            base_key = self._generate_key(candle_request.sec_type, candle_request.symbol, candle_request.bar_size)
            pipeline = self.redis_client.pipeline()
            for field in OHLCV_FIELDS:
                pipeline.ts().del_range(
                    f"{base_key}:{field}", candle_request.from_time, candle_request.to_time  # noqa E231
                )  # noqa E231
            pipeline.execute()

            if all(
                self.redis_client.ts().range(f"{base_key}:{field}", "-", "+") == []  # noqa E231
                for field in OHLCV_FIELDS  # noqa E231
            ):  # noqa E231
                self.created_ts_cache.discard(
                    (candle_request.sec_type, candle_request.symbol, candle_request.bar_size)
                )

        except Exception as e:
            self.logger.error("Error deleting candles: %s", e)
            raise OhlcvError(f"Failed to delete candles: {e}")

    @staticmethod
    def date_to_timestamp(date_string: str, timezone: str = "US/Eastern") -> int:
        """Convert date string to timestamp."""
        try:
            date_parts = date_string.split()
            date_time_str = " ".join(date_parts[:2])
            timezone_str = date_parts[2] if len(date_parts) > 2 else timezone

            dt = datetime.strptime(date_time_str, "%Y%m%d %H:%M:%S" if " " in date_time_str else "%Y%m%d")  # noqa E231

            try:
                tz = pytz.timezone(timezone_str)
            except pytz.exceptions.UnknownTimeZoneError:
                tz = pytz.timezone(timezone)

            localized_dt = tz.localize(dt)
            utc_dt = localized_dt.astimezone(pytz.UTC)

            return int(utc_dt.timestamp() * 1000)
        except Exception as e:
            raise TimestampError(f"Failed to convert date to timestamp: {e}")

    def get_latest_candle(self, sec_type: str, symbol: str, bar_size: str) -> Optional[OhlcvCandleData]:
        """Get latest candle."""
        try:
            base_key = self._generate_key(sec_type, symbol, bar_size)
            latest_data = {}
            for field in OHLCV_FIELDS:
                data = self.redis_client.ts().get(f"{base_key}:{field}")  # noqa E231
                if data:
                    latest_data[field] = data[1]
                    if field == "open":
                        latest_data["timestamp"] = data[0]

            return OhlcvCandleData(**latest_data) if latest_data else None
        except Exception as e:
            self.logger.error("Error getting latest candle: %s", e)
            raise OhlcvError(f"Failed to get latest candle: {e}")

    def get_candle_count(self, sec_type: str, symbol: str, bar_size: str) -> int:
        """Get candle count."""
        try:
            base_key = self._generate_key(sec_type, symbol, bar_size)
            info = self.redis_client.ts().info(f"{base_key}:open")  # noqa E231
            return info.total_samples
        except Exception as e:
            self.logger.error("Error getting candle count: %s", e)
            raise OhlcvError(f"Failed to get candle count: {e}")

    def clear_cache(self):
        """Clear cache."""
        self.ts_key_cache.clear()
        self.created_ts_cache.clear()

    def is_ts_created(self, sec_type: str, symbol: str, bar_size: str) -> bool:
        """Check if time series is created."""
        return (sec_type, symbol, bar_size) in self.created_ts_cache

    def get_symbols(self) -> List[str]:
        """Get symbols."""
        metadata = self.redis_client.hgetall(self.metadata_key)
        return list(set(key.split(":")[1] for key in metadata.keys()))

    def get_symbols_and_bar_sizes(self, sec_type: str = "STK") -> Dict[str, List[Tuple[str, int]]]:
        """Get symbols and bar sizes."""
        metadata = self.redis_client.hgetall(self.metadata_key)
        symbol_bar_sizes = {}
        for key, value in metadata.items():
            load_sec_type, symbol = key.split(":")
            if sec_type != load_sec_type:
                continue
            bar_sizes = [self._unsanitize_bar_size(bar_size) for bar_size in value.split(",")]
            symbol_data = [(bar_size, self._get_min_timestamp(sec_type, symbol, bar_size)) for bar_size in bar_sizes]
            symbol_bar_sizes[symbol] = symbol_data
        return symbol_bar_sizes

    def _get_min_timestamp(self, sec_type: str, symbol: str, bar_size: str) -> int:
        """Get minimum timestamp for a symbol and bar size."""
        base_key = self._generate_key(sec_type, symbol, bar_size)
        try:
            result = self.redis_client.ts().range(f"{base_key}:open", "-", "+", count=1)  # noqa E231
            return result[0][0] if result else 0
        except OhlcvError as e:
            self.logger.error("Error getting min timestamp for %s, %s, error: %s", symbol, bar_size, str(e))
            return 0
