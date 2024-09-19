"""Candle request schema."""

from pydantic import BaseModel


class CandleRequest(BaseModel):
    """Candle request model."""

    sec_type: str
    symbol: str
    bar_size: str
    from_time: int
    to_time: int
