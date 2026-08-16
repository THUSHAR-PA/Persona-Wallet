from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
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
    return create_transaction(
        db=db,
        from_account_id=transaction_data.from_account_id,
        to_account_id=transaction_data.to_account_id,
        amount=transaction_data.amount,
        category=transaction_data.category,
        description=transaction_data.description,
    )


@router.get("/", response_model=list[TransactionRead])
def get_transactions(
    db: Session = Depends(get_db),
):
    from app.models.transaction import Transaction

    return db.query(Transaction).order_by(
        Transaction.created_at.desc()
    ).all()