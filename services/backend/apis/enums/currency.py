"""Currency Enum."""

from enum import Enum


class Currency(str, Enum):
    """Return Currency Enum."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
