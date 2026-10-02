from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction

router = APIRouter(
    prefix="/integration",
    tags=["Integration"],
)


def _serialize_transaction(transaction: Transaction, current_user: User):
    is_outgoing = transaction.from_account.owner_id == current_user.id
    counterparty = (
        transaction.to_account.owner.username
        if is_outgoing
        else transaction.from_account.owner.username
    )

    return {
        "id": transaction.id,
        "from_account_id": transaction.from_account_id,
        "to_account_id": transaction.to_account_id,
        "amount": transaction.amount,
        "category": transaction.category,
        "description": transaction.description,
        "status": transaction.status,
        "created_at": transaction.created_at,
        "direction": "OUTFLOW" if is_outgoing else "INFLOW",
        "counterparty": counterparty,
    }


@router.get("/financial-summary")
def get_financial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = (
        db.query(Account)
        .filter(Account.owner_id == current_user.id)
        .all()
    )

    account_ids = [account.id for account in accounts]

    transactions = (
        db.query(Transaction)
        .filter(
            (Transaction.from_account_id.in_(account_ids))
            | (Transaction.to_account_id.in_(account_ids))
        )
        .order_by(Transaction.created_at.desc())
        .all()
        if account_ids
        else []
    )

    total_balance = sum(
        (account.balance or Decimal("0"))
        for account in accounts
        if not account.is_system
    )

    total_inflow = Decimal("0")
    total_outflow = Decimal("0")
    category_spend: dict[str, Decimal] = {}

    for transaction in transactions:
        amount = transaction.amount or Decimal("0")

        if transaction.to_account.owner_id == current_user.id:
            total_inflow += amount

        if transaction.from_account.owner_id == current_user.id:
            total_outflow += amount
            category_name = transaction.category.value
            category_spend[category_name] = (
                category_spend.get(category_name, Decimal("0")) + amount
            )

    cash_flow = total_inflow - total_outflow
    savings_rate = (
        (cash_flow / total_inflow * Decimal("100"))
        if total_inflow > 0
        else Decimal("0")
    )

    largest_expense_category = None
    if category_spend:
        largest_expense_category = max(
            category_spend.items(),
            key=lambda item: item[1],
        )[0]

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
        },
        "accounts": [
            {
                "id": account.id,
                "name": account.name,
                "account_type": account.account_type,
                "balance": account.balance,
                "currency": account.currency,
            }
            for account in accounts
            if not account.is_system
        ],
        "metrics": {
            "total_balance": total_balance,
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "net_cash_flow": cash_flow,
            "savings_rate_percent": round(savings_rate, 2),
            "transaction_count": len(transactions),
            "largest_expense_category": largest_expense_category,
        },
        "category_spend": [
            {
                "category": category,
                "amount": amount,
            }
            for category, amount in sorted(
                category_spend.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ],
        "recent_transactions": [
            _serialize_transaction(transaction, current_user)
            for transaction in transactions[:10]
        ],
        "transactions": [
            _serialize_transaction(transaction, current_user)
            for transaction in transactions
        ],
    }
