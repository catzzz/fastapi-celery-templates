"""Candle request schema."""

from pydantic import BaseModel

from .contract_request import ExtendContractRequest


class CandleRequest(BaseModel):
    """Class Candle request model."""

    extend_contract_request: ExtendContractRequest
    from_time: int
    to_time: int
