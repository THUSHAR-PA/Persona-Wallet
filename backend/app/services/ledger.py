
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.enums.transaction_status import TransactionStatus


def create_transaction(
    db: Session,
    current_user: User,
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    category,
    description: str | None = None,
):
    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Transaction amount must be greater than zero."
        )

    from_account = db.query(Account).filter(
        Account.id == from_account_id
    ).first()

    to_account = db.query(Account).filter(
        Account.id == to_account_id
    ).first()

    if not from_account:
        raise HTTPException(
            status_code=404,
            detail="Source account not found."
        )

    if not to_account:
        raise HTTPException(
            status_code=404,
            detail="Destination account not found."
        )

    # The logged-in user must own the source account
    if from_account.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only transfer money from your own account."
        )

    # Prevent transferring to the exact same account
    if from_account_id == to_account_id:
        raise HTTPException(
            status_code=400,
            detail="Source and destination accounts must be different."
        )

    if from_account.balance < amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance."
        )

    from_account.balance -= amount
    to_account.balance += amount

    transaction = Transaction(
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount=amount,
        category=category,
        description=description,
        status=TransactionStatus.SUCCESS,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction
