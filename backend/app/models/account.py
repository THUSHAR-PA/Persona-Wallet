from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Boolean,
    Enum,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.account_type import AccountType


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    name = Column(String(100), nullable=False)

    account_type = Column(
        Enum(AccountType),
        nullable=False,
    )

    balance = Column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    currency = Column(
        String(10),
        default="INR",
        nullable=False,
    )

    is_system = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    owner = relationship(
        "User",
        back_populates="accounts",
    )

    outgoing_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.from_account_id",
        back_populates="from_account",
    )

    incoming_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.to_account_id",
        back_populates="to_account",
    )