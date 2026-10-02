
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

    # Lock both accounts in the same order as statement imports. A transfer and
    # import cannot race to overwrite each other's balance on PostgreSQL.
    locked = db.query(Account).filter(Account.id.in_([from_account_id, to_account_id])).order_by(
        Account.id
    ).with_for_update().populate_existing().all()
    by_id = {account.id: account for account in locked}
    from_account = by_id.get(from_account_id)
    to_account = by_id.get(to_account_id)

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

    if from_account.currency != to_account.currency:
        raise HTTPException(400, "Transfers require accounts in the same currency.")

    if from_account.balance < amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance."
        )

    if to_account.balance + amount >= Decimal("10000000000000"):
        raise HTTPException(400, "Destination balance exceeds the supported amount.")

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
