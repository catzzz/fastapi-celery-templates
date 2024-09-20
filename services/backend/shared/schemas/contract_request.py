"""Contract request schema."""

from pydantic import (
    BaseModel,
    Field,
)
from shared.enums.bar_size import BarSize
from shared.enums.currency import Currency
from shared.enums.exchange import Exchange
from shared.enums.sec_type import SecType


class ContractRequest(BaseModel):
    """Contract request schema."""

    symbol: str
    sec_type: SecType
    currency: Currency
    exchange: Exchange = Field(Exchange.SMART, description="Exchange name")


class ExtendContractRequest(ContractRequest):
    """Extend contract request schema."""

    bar_size: BarSize
