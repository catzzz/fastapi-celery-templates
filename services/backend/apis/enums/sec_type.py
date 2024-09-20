"""Sectype Enum."""

from enum import Enum


class SecType(str, Enum):
    """Class SecType Enum."""

    STK = "STK"
    OPT = "OPT"
    FUT = "FUT"
    IND = "IND"
    CASH = "CASH"
    CRYPTO = "CRYPTO"
