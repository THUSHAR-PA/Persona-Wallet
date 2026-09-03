
from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
)
from app.services.ledger import create_transaction


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.post("/", response_model=TransactionRead)
def create_transaction_api(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
):
    transaction = create_transaction(
        db=db,
        from_account_id=transaction_data.from_account_id,
        to_account_id=transaction_data.to_account_id,
        amount=transaction_data.amount,
        category=transaction_data.category,
        description=transaction_data.description,
    )

    from_user = db.query(User).filter(
        User.id == transaction.from_account.owner_id
    ).first()

    to_user = db.query(User).filter(
        User.id == transaction.to_account.owner_id
    ).first()

    return {
        "id": transaction.id,
        "from_account_id": transaction.from_account_id,
        "to_account_id": transaction.to_account_id,
        "amount": transaction.amount,
        "category": transaction.category,
        "description": transaction.description,
        "status": transaction.status,
        "from_account": {
            "id": transaction.from_account.id,
            "name": transaction.from_account.name,
            "owner_username": from_user.username,
        },
        "to_account": {
            "id": transaction.to_account.id,
            "name": transaction.to_account.name,
            "owner_username": to_user.username,
        },
    }


@router.get("/", response_model=list[TransactionRead])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = db.query(Transaction).filter(
        or_(
            Transaction.from_account.has(
                owner_id=current_user.id
            ),
            Transaction.to_account.has(
                owner_id=current_user.id
            ),
        )
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    result = []

    for transaction in transactions:
        from_user = db.query(User).filter(
            User.id == transaction.from_account.owner_id
        ).first()

        to_user = db.query(User).filter(
            User.id == transaction.to_account.owner_id
        ).first()

        result.append({
            "id": transaction.id,
            "from_account_id": transaction.from_account_id,
            "to_account_id": transaction.to_account_id,
            "amount": transaction.amount,
            "category": transaction.category,
            "description": transaction.description,
            "status": transaction.status,
            "from_account": {
                "id": transaction.from_account.id,
                "name": transaction.from_account.name,
                "owner_username": from_user.username,
            },
            "to_account": {
                "id": transaction.to_account.id,
                "name": transaction.to_account.name,
                "owner_username": to_user.username,
            },
        })

    return result
