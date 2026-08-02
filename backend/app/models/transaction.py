from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Numeric,
    Enum,
    String,
    DateTime,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.transaction_category import TransactionCategory
from app.enums.transaction_status import TransactionStatus


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    from_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    to_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    category = Column(
        Enum(TransactionCategory),
        nullable=False,
    )

    description = Column(
        String(255),
    )

    status = Column(
        Enum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    from_account = relationship(
        "Account",
        foreign_keys=[from_account_id],
        back_populates="outgoing_transactions",
    )

    to_account = relationship(
        "Account",
        foreign_keys=[to_account_id],
        back_populates="incoming_transactions",
    )