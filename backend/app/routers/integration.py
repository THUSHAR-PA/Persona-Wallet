from decimal import Decimal

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.enums.transaction_status import TransactionStatus
from app.services.financial_analysis import financial_analysis

router = APIRouter(
    prefix="/integration",
    tags=["Integration"],
)


def _serialize_transaction(transaction: Transaction, current_user: User):
    from_current_user = transaction.from_account.owner_id == current_user.id
    to_current_user = transaction.to_account.owner_id == current_user.id

    if from_current_user and to_current_user:
        direction = "INTERNAL"
        counterparty = transaction.to_account.name
    elif from_current_user:
        direction = "OUTFLOW"
        counterparty = (
            transaction.to_account.owner.username
            if transaction.to_account.owner
            else transaction.to_account.name
        )
    else:
        direction = "INFLOW"
        counterparty = (
            transaction.from_account.owner.username
            if transaction.from_account.owner
            else transaction.from_account.name
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
        "direction": direction,
        "counterparty": counterparty,
    }


@router.get("/financial-summary")
def get_financial_summary(
    months: int = Query(6, ge=1, le=24),
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if end_date and end_date > date.today():
        raise HTTPException(422, "Analysis end date cannot be in the future.")
    accounts = db.query(Account).filter(Account.owner_id == current_user.id).all()

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
        if not account.is_system and account.currency == "INR"
    )

    total_inflow = Decimal("0")
    total_outflow = Decimal("0")
    category_spend: dict[str, Decimal] = {}

    for transaction in transactions:
        if transaction.status != TransactionStatus.SUCCESS:
            continue
        amount = transaction.amount or Decimal("0")

        from_current_user = transaction.from_account.owner_id == current_user.id
        to_current_user = transaction.to_account.owner_id == current_user.id

        if (
            to_current_user
            and not from_current_user
            and transaction.to_account.currency == "INR"
        ):
            total_inflow += amount

        if (
            from_current_user
            and not to_current_user
            and transaction.from_account.currency == "INR"
        ):
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
        "financial_twin": financial_analysis(
            db, current_user, accounts, transactions, months, end_date
        ),
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
            "currency": "INR",
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
