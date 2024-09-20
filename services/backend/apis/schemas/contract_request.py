"""Contract request schema."""

from apis.enums.bar_size import BarSize
from apis.enums.currency import Currency
from apis.enums.exchange import Exchange
from apis.enums.sec_type import SecType
from pydantic import (
    BaseModel,
    Field,
)


class ContractRequest(BaseModel):
    """Contract request schema."""

    symbol: str
    sec_type: SecType
    currency: Currency
    exchange: Exchange = Field(Exchange.SMART, description="Exchange name")


class ExtendContractRequest(ContractRequest):
    """Extend contract request schema."""

    bar_size: BarSize
