"""Exchange enum."""
from enum import Enum


class Exchange(str, Enum):
    """Class for Exchange Enum."""

    SMART = "SMART"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    AMEX = "AMEX"
