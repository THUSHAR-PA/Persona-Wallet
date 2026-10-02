from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Money = Annotated[Decimal, Field(ge=0, max_digits=15, decimal_places=2)]


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    employer: str = Field(default="", max_length=120)
    occupation: str = Field(default="", max_length=120)
    monthly_salary: Money = Decimal("0")
    other_monthly_income: Money = Decimal("0")
    monthly_expense_budget: Money = Decimal("0")
    investment_value: Money = Decimal("0")
    property_value: Money = Decimal("0")
    other_asset_value: Money = Decimal("0")
    dependants: int = Field(default=0, ge=0, le=100)


class LiabilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    kind: Literal[
        "MORTGAGE",
        "PERSONAL_LOAN",
        "EDUCATION_LOAN",
        "VEHICLE_LOAN",
        "CREDIT_CARD",
        "OTHER",
    ]
    lender: str = Field(min_length=1, max_length=120)
    original_amount: Money
    outstanding_amount: Money
    annual_interest_rate: Decimal = Field(ge=0, le=100, max_digits=6, decimal_places=3)
    monthly_payment: Money
    remaining_months: int = Field(ge=0, le=600)
    as_of_date: date

    @model_validator(mode="after")
    def check_date(self):
        if self.as_of_date > date.today():
            raise ValueError("Balance date cannot be in the future.")
        return self


class BankAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    bank_name: str = Field(min_length=1, max_length=120)
    last_four: str = Field(default="", pattern=r"^(\d{4})?$")
    currency: Literal["INR"] = "INR"
    wallet_account_id: int | None = Field(default=None, gt=0)
