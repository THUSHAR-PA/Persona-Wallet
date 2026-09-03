
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
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
    current_user: User = Depends(get_current_user),
):
    return create_transaction(
        db=db,
        current_user=current_user,
        from_account_id=transaction_data.from_account_id,
        to_account_id=transaction_data.to_account_id,
        amount=transaction_data.amount,
        category=transaction_data.category,
        description=transaction_data.description,
    )


@router.get("/", response_model=list[TransactionRead])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.transaction import Transaction

    return db.query(Transaction).join(
        Transaction.from_account
    ).filter(
        Transaction.from_account.has(owner_id=current_user.id)
    ).order_by(
        Transaction.created_at.desc()
    ).all()
