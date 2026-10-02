"""Financial details and imported history attached to spendable bank accounts."""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.core.database import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    employer = Column(String(120), nullable=False, default="")
    occupation = Column(String(120), nullable=False, default="")
    monthly_salary = Column(Numeric(15, 2), nullable=False, default=0)
    other_monthly_income = Column(Numeric(15, 2), nullable=False, default=0)
    monthly_expense_budget = Column(Numeric(15, 2), nullable=False, default=0)
    investment_value = Column(Numeric(15, 2), nullable=False, default=0)
    property_value = Column(Numeric(15, 2), nullable=False, default=0)
    other_asset_value = Column(Numeric(15, 2), nullable=False, default=0)
    dependants = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Liability(Base):
    __tablename__ = "financial_liabilities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    kind = Column(String(30), nullable=False)
    lender = Column(String(120), nullable=False)
    original_amount = Column(Numeric(15, 2), nullable=False)
    outstanding_amount = Column(Numeric(15, 2), nullable=False)
    annual_interest_rate = Column(Numeric(6, 3), nullable=False)
    monthly_payment = Column(Numeric(15, 2), nullable=False)
    remaining_months = Column(Integer, nullable=False)
    as_of_date = Column(Date, nullable=False)


class BankAccount(Base):
    __tablename__ = "statement_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_statement_account_name"),
        UniqueConstraint("wallet_account_id", name="uq_statement_wallet_account"),
    )
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    bank_name = Column(String(120), nullable=False)
    last_four = Column(String(4), nullable=False, default="")
    currency = Column(String(3), nullable=False, default="INR")
    wallet_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)


class StatementImport(Base):
    __tablename__ = "statement_imports"
    __table_args__ = (
        UniqueConstraint("account_id", "file_hash", name="uq_statement_file"),
    )
    id = Column(Integer, primary_key=True)
    account_id = Column(
        Integer, ForeignKey("statement_accounts.id"), nullable=False, index=True
    )
    filename = Column(String(200), nullable=False)
    file_hash = Column(String(64), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    opening_balance = Column(Numeric(15, 2), nullable=True)
    closing_balance = Column(Numeric(15, 2), nullable=True)
    imported_rows = Column(Integer, nullable=False)
    duplicate_rows = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StatementEntry(Base):
    __tablename__ = "statement_entries"
    __table_args__ = (
        UniqueConstraint("account_id", "fingerprint", name="uq_statement_entry"),
    )
    id = Column(Integer, primary_key=True)
    account_id = Column(
        Integer, ForeignKey("statement_accounts.id"), nullable=False, index=True
    )
    import_id = Column(Integer, ForeignKey("statement_imports.id"), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=False)
    reference = Column(String(120), nullable=False, default="")
    direction = Column(String(10), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    category = Column(String(30), nullable=False)
    balance = Column(Numeric(15, 2), nullable=True)
