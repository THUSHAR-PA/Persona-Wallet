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
    )

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
        ],
        "total_balance": total_balance,
        "transactions": [
            {
                "id": transaction.id,
                "from_account_id": transaction.from_account_id,
                "to_account_id": transaction.to_account_id,
                "amount": transaction.amount,
                "category": transaction.category,
                "description": transaction.description,
                "status": transaction.status,
                "created_at": transaction.created_at,
            }
            for transaction in transactions
        ],
    }