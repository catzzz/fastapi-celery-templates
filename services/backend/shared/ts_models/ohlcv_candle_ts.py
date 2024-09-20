"""OHLCV Candle Time Series model."""

from datetime import datetime
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    override,
)

import pytz
from pydantic import (
    BaseModel,
    Field,
)
from shared.enums.bar_size import BarSize
from shared.enums.currency import Currency
from shared.enums.sec_type import SecType
from shared.schemas.candle_request import CandleRequest
from shared.schemas.contract_request import ExtendContractRequest

from .base_ts_model import (
    BaseTimeSeriesModel,
    TimeSeriesModelException,
)


class BarSizeMinTimestamp(BaseModel):
    """Bar size and minimum timestamp."""

    bar_size: str
    min_timestamp: int


class TimeSeriesSymbolsBarSizeKey(BaseModel):
    """Time series symbols and bar sizes key."""

    symbol: str
    bar_size_min_timestamps: List[BarSizeMinTimestamp]


class OhlcvCandleData(BaseModel):
    """OHLCV Candle Data."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    wap: Optional[float] = Field(None, description="Weighted average price.")
    barcount: Optional[int] = Field(None, description="Number of trades.")

    @staticmethod
    def us_estern_date_to_timestamp(date_string: str, timezone: str = "US/Eastern") -> int:
        """Convert IBKR date string to timestamp."""
        try:
            date_parts = date_string.split()
            date_time_str = " ".join(date_parts[:2])
            timezone_str = date_parts[2] if len(date_parts) > 2 else timezone

            dt = datetime.strptime(date_time_str, "%Y%m%d %H:%M:%S" if " " in date_time_str else "%Y%m%d")

            try:
                tz = pytz.timezone(timezone_str)
            except pytz.exceptions.UnknownTimeZoneError:
                tz = pytz.timezone(timezone)

            localized_dt = tz.localize(dt)
            utc_dt = localized_dt.astimezone(pytz.UTC)

            return int(utc_dt.timestamp() * 1000)
        except Exception as e:
            raise TimeSeriesModelException(f"Failed to convert date to timestamp: {e}")


class OhlcvCandleException(TimeSeriesModelException):
    """OHLCV Candle Exception."""


class OhlcvCandleTS(BaseTimeSeriesModel):
    """OHLCV Candle Time Series model."""

    def __init__(self, debug: bool = False, expire: Optional[int] = None):
        super().__init__(prefix="candle_ts", debug=debug, expire=expire)

    @override
    # pylint: disable=arguments-differ
    def get_key(self, extend_contract_request: ExtendContractRequest) -> str:
        """Get key for time series."""
        sec_type = extend_contract_request.sec_type.value
        symbol = extend_contract_request.symbol
        bar_size = extend_contract_request.bar_size.value
        currency = extend_contract_request.currency.value
        if not all([sec_type, symbol, bar_size, currency]):
            raise OhlcvCandleException("Invalid contract request")
        return super().get_key(sec_type, currency, symbol, bar_size)

    @override
    # pylint: disable=arguments-differ
    def create_ts(self, extend_contract_request: ExtendContractRequest) -> None:
        """Create time series."""
        sec_type = extend_contract_request.sec_type.value
        symbol = extend_contract_request.symbol
        bar_size = extend_contract_request.bar_size.value
        currency = extend_contract_request.currency.value
        if not all([sec_type, symbol, bar_size, currency]):
            raise OhlcvCandleException("Invalid contract request")
        key = (sec_type, currency, symbol, bar_size)
        if key in self.created_ts_cache:
            return

        try:
            base_key = self.get_key(extend_contract_request)
            self.redis_client.ts().create(base_key)

            if self.expire:
                self.redis_client.expire(base_key, self.expire)

            self._update_metadata(sec_type, currency, symbol, bar_size)
            self.created_ts_cache.add(key)
        except Exception as e:
            self.logger.error("Error creating time series: %s", e)
            raise OhlcvCandleException(f"Failed to create time series: {e}")

    @override
    # pylint: disable=arguments-differ
    def add_data(self, data: OhlcvCandleData, extend_contract_request: ExtendContractRequest) -> None:
        """Add data to time series."""
        sec_type = extend_contract_request.sec_type.value
        symbol = extend_contract_request.symbol
        bar_size = extend_contract_request.bar_size.value
        currency = extend_contract_request.currency.value
        if not all([sec_type, symbol, bar_size, currency]):
            raise TimeSeriesModelException("Invalid contract request")

        try:
            self.create_ts(extend_contract_request)
            key = self.get_key(extend_contract_request)

            # Check if data already exists
            existing_data = self.redis_client.ts().get(key, data.timestamp)
            if existing_data:
                self.logger.warning("Data already exists for timestamp %s", data.timestamp)
                raise TimeSeriesModelException(f"Data already exists for timestamp {data.timestamp}")

            # Store all OHLCV data as a single value
            value = (
                f"{data.open},{data.high},{data.low},{data.close},"  # noqa E231
                f"{data.volume},{data.wap or -1},{data.barcount or -1}"  # noqa E231
            )
            self.redis_client.ts().add(key, data.timestamp, value)
            self.logger.debug("Successfully added candle for timestamp %s", data.timestamp)

        except TimeSeriesModelException:
            raise
        except Exception as e:
            self.logger.error("Failed to add candle: %s", str(e), exc_info=True)
            raise TimeSeriesModelException(f"Failed to add candle: {e}")

    @override
    # pylint: disable=arguments-differ
    def get_data(self, candle_request: CandleRequest) -> List[OhlcvCandleData]:
        """Get data from time series."""
        try:
            key = self.get_key(candle_request.extend_contract_request)
            self.logger.debug("Generated key: %s", key)

            results = self._fetch_results(key, candle_request)
            if not results:
                self.logger.info("No data found for %s", candle_request)
                return []

            candles = self._process_results(results)
            self.logger.debug("Generated candles: %s", candles)
            return candles
        except Exception as e:
            self.logger.error("Error getting candles: %s ", str(e), exc_info=True)
            raise TimeSeriesModelException(f"Failed to get candles: {e}")

    def _fetch_results(self, key: str, candle_request: CandleRequest):
        results = self.redis_client.ts().range(key, candle_request.from_time, candle_request.to_time)
        self.logger.debug("Query results: %s", results)
        return results

    def _process_results(self, results: List[Tuple[int, str]]) -> List[OhlcvCandleData]:
        return [self._create_candle_data(*result) for result in results]

    def _create_candle_data(self, timestamp: int, value: str) -> OhlcvCandleData:
        open_price, high, low, close, volume, wap, barcount = map(float, value.split(","))
        return OhlcvCandleData(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            wap=None if wap == -1 else wap,
            barcount=None if barcount == -1 else int(barcount),
        )

    @override
    # pylint: disable=arguments-differ
    def get_latest_data(self, extend_contract_request: ExtendContractRequest) -> Optional[OhlcvCandleData]:
        """Get latest data from time series."""
        try:
            key = self.get_key(extend_contract_request)
            result = self.redis_client.ts().get(key)
            if result:
                timestamp, value = result
                open_price, high, low, close, volume, wap, barcount = map(float, value.split(","))
                return OhlcvCandleData(
                    timestamp=timestamp,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    wap=None if wap == -1 else wap,
                    barcount=None if barcount == -1 else int(barcount),
                )
            return None
        except Exception as e:
            self.logger.error("Error getting latest candle: %s", e)
            raise TimeSeriesModelException(f"Failed to get latest candle: {e}")

    @override
    # pylint: disable=arguments-differ
    def _update_metadata(self, sec_type: str, currency: str, symbol: str, bar_size: str) -> None:
        """Update metadata with bar size."""
        metadata_key = f"{sec_type}:{currency}:{symbol}"  # noqa E231
        try:
            current_bar_sizes = self.redis_client.hget(self.metadata_key, metadata_key)
            sanitized_bar_size = self._sanitize_key(bar_size)
            if current_bar_sizes:
                bar_sizes = set(current_bar_sizes.split(","))
                bar_sizes.add(sanitized_bar_size)
                self.redis_client.hset(self.metadata_key, metadata_key, ",".join(sorted(bar_sizes)))
            else:
                self.redis_client.hset(self.metadata_key, metadata_key, sanitized_bar_size)
        except Exception as e:
            self.logger.error("Failed to update metadata for key %s: %s", metadata_key, str(e))
            raise OhlcvCandleException(f"Failed to update metadata for key {metadata_key}: {str(e)}")

    def get_symbols(self) -> List[str]:
        """Get symbols."""
        metadata = self.redis_client.hgetall(self.metadata_key)
        return list(set(key.split(":")[2] for key in metadata.keys()))

    def _get_min_timestamp(self, extend_contract_request: ExtendContractRequest) -> int:
        """Get min timestamp."""
        key = self.get_key(extend_contract_request)
        try:
            result = self.redis_client.ts().range(key, "-", "+", count=1)
            return result[0][0] if result else 0
        except OhlcvCandleException as e:
            self.logger.error(
                "Error getting min timestamp for %s, %s, %s, error: %s",
                extend_contract_request.symbol,
                extend_contract_request.bar_size,
                extend_contract_request.currency,
                str(e),
            )
            return 0

    def _unsanitize_bar_size(self, value: str) -> str:
        """Unsanitize bar size."""
        return value.replace("_", " ")

    def get_symbols_and_bar_sizes(
        self, sec_type: str = "STK", currency: str = "USD"
    ) -> Dict[str, List[Tuple[str, int]]]:
        """Get symbols and bar sizes."""
        try:
            metadata = self.redis_client.hgetall(self.metadata_key)
            return self._process_metadata(metadata, sec_type, currency)
        except OhlcvCandleException as e:
            self.logger.error("Error getting symbols and bar sizes: %s", str(e))
            return {}

    def _process_metadata(
        self, metadata: Dict[str, str], sec_type: str, currency: str
    ) -> Dict[str, List[Tuple[str, int]]]:
        symbol_bar_sizes = {}
        for key, value in metadata.items():
            symbol_data = self._process_symbol_data(key, value, sec_type, currency)
            if symbol_data:
                symbol_bar_sizes[symbol_data[0]] = symbol_data[1]
        return symbol_bar_sizes

    def _process_symbol_data(
        self, key: str, value: str, sec_type: str, currency: str
    ) -> Optional[Tuple[str, List[Tuple[str, int]]]]:
        load_sec_type, load_currency, symbol = key.split(":")
        if sec_type != load_sec_type or currency != load_currency:
            return None

        bar_sizes = [self._unsanitize_bar_size(bar_size) for bar_size in value.split(",")]
        symbol_data = self._get_symbol_bar_sizes(load_sec_type, load_currency, symbol, bar_sizes)
        return (symbol, symbol_data) if symbol_data else None

    def _get_symbol_bar_sizes(
        self, sec_type: str, currency: str, symbol: str, bar_sizes: List[str]
    ) -> List[Tuple[str, int]]:
        symbol_data = []
        for bar_size in bar_sizes:
            try:
                extend_contract_request = ExtendContractRequest(
                    sec_type=SecType(sec_type),
                    currency=Currency(currency),
                    symbol=symbol,
                    bar_size=BarSize(bar_size),
                )
                min_timestamp = self._get_min_timestamp(extend_contract_request)
                symbol_data.append((bar_size, min_timestamp))
            except Exception as e:
                raise OhlcvCandleException(f"Failed to get min timestamp for {symbol}, {bar_size}: {e}")
        return symbol_data
