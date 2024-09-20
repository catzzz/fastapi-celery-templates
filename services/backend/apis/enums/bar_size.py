"""Barsize Enum."""

from enum import Enum


class BarSize(str, Enum):
    """Retuen Barsize Enum."""

    ONE_MINUTE = "1 min"
    FIVE_MINUTES = "5 mins"
    TEN_MINUTES = "10 mins"
    FIFTEEN_MINUTES = "15 mins"
    TWENTY_MINUTES = "20 mins"
    ONE_HOUR = "1 hour"
    ONE_DAY = "1 day"
