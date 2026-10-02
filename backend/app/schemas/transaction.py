
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.enums.transaction_category import TransactionCategory
from app.enums.transaction_status import TransactionStatus


class TransactionCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    category: TransactionCategory
    description: str | None = Field(default=None, max_length=255)


class TransactionAccountInfo(BaseModel):
    id: int
    name: str
    owner_username: str


class TransactionRead(BaseModel):
    id: int
    from_account_id: int
    to_account_id: int
    amount: Decimal
    category: TransactionCategory
    description: str | None
    status: TransactionStatus

    from_account: TransactionAccountInfo
    to_account: TransactionAccountInfo
