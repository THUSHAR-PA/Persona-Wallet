from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.enums.account_type import AccountType


class AccountCreate(BaseModel):
    name: str
    account_type: AccountType = AccountType.PERSONAL
    balance: Decimal = Decimal("0.00")
    currency: str = "INR"


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_type: AccountType
    balance: Decimal
    currency: str
    is_system: bool


class AccountDestinationRead(BaseModel):
    id: int
    name: str
    account_type: AccountType
    owner_username: str