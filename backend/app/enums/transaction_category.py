from enum import Enum


class TransactionCategory(str, Enum):
    SALARY = "SALARY"
    PURCHASE = "PURCHASE"
    TRANSFER = "TRANSFER"
    RENT = "RENT"
    INVESTMENT = "INVESTMENT"
    REFUND = "REFUND"
    SUBSCRIPTION = "SUBSCRIPTION"
    TAX = "TAX"
    OTHER = "OTHER"