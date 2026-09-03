from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.schemas.account import (
    AccountCreate,
    AccountRead,
    AccountDestinationRead,
)
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)


@router.post("/", response_model=AccountRead)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_account = db.query(Account).filter(
        Account.name == account_data.name
    ).first()

    if existing_account:
        raise HTTPException(
            status_code=409,
            detail=f"An account named '{account_data.name}' already exists."
        )

    account = Account(
        owner_id=current_user.id,
        name=account_data.name,
        account_type=account_data.account_type,
        balance=account_data.balance,
        currency=account_data.currency,
        is_system=False,
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.get("/", response_model=list[AccountRead])
def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Account).filter(
        Account.owner_id == current_user.id,
        Account.is_system == False,
    ).all()


@router.get(
    "/destinations",
    response_model=list[AccountDestinationRead]
)
def get_destination_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = (
        db.query(Account, User.username)
        .join(User, Account.owner_id == User.id)
        .filter(
            Account.is_system == False,
        )
        .all()
    )

    return [
        {
            "id": account.id,
            "name": account.name,
            "account_type": account.account_type,
            "owner_username": username,
        }
        for account, username in accounts
    ]


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.owner_id == current_user.id,
        Account.is_system == False,
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    return account