from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)


@router.post("/", response_model=AccountRead)
@router.post("/", response_model=AccountRead)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db)
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
        name=account_data.name,
        account_type=account_data.account_type,
        balance=account_data.balance,
        currency=account_data.currency,
        is_system=False
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.get("/", response_model=list[AccountRead])
def get_accounts(
    db: Session = Depends(get_db)
):
    return db.query(Account).all()


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(
        Account.id == account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    return account