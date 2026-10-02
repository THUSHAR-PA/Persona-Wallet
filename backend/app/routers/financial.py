import json
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.financial import (
    BankAccount,
    FinancialProfile,
    Liability,
    StatementEntry,
    StatementImport,
)
from app.models.user import User
from app.schemas.financial import BankAccountInput, LiabilityInput, ProfileInput
from app.services.statements import (
    CATEGORIES,
    MAX_FILE_BYTES,
    StatementError,
    parse_statement,
)

router = APIRouter(prefix="/financial", tags=["Financial twin"])
SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample-bank-statement.csv"


def record_dict(record):
    return {
        column.name: getattr(record, column.name) for column in record.__table__.columns
    }


def owned(db, model, record_id, user):
    record = (
        db.query(model).filter(model.id == record_id, model.user_id == user.id).first()
    )
    if not record:
        raise HTTPException(404, "Record not found.")
    return record


def commit(db):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            409,
            "This record already exists or was imported concurrently. Refresh and retry.",
        ) from exc


@router.get("/profile")
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.get(FinancialProfile, user.id)
    return {"profile": record_dict(profile) if profile else None, "currency": "INR"}


@router.put("/profile")
def save_profile(
    data: ProfileInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = db.get(FinancialProfile, user.id)
    if profile is None:
        profile = FinancialProfile(user_id=user.id)
        db.add(profile)
    for key, value in data.model_dump().items():
        setattr(profile, key, value)
    commit(db)
    db.refresh(profile)
    return record_dict(profile)


@router.get("/liabilities")
def get_liabilities(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return [
        record_dict(row)
        for row in db.query(Liability)
        .filter_by(user_id=user.id)
        .order_by(Liability.id)
        .all()
    ]


@router.post("/liabilities", status_code=201)
def add_liability(
    data: LiabilityInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = Liability(user_id=user.id, **data.model_dump())
    db.add(row)
    commit(db)
    db.refresh(row)
    return record_dict(row)


@router.put("/liabilities/{record_id}")
def update_liability(
    record_id: int,
    data: LiabilityInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = owned(db, Liability, record_id, user)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    commit(db)
    return record_dict(row)


@router.delete("/liabilities/{record_id}", status_code=204)
def delete_liability(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.delete(owned(db, Liability, record_id, user))
    commit(db)


@router.get("/bank-accounts")
def get_bank_accounts(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    result = []
    for account in (
        db.query(BankAccount).filter_by(user_id=user.id).order_by(BankAccount.id).all()
    ):
        imports = (
            db.query(StatementImport)
            .filter_by(account_id=account.id)
            .order_by(StatementImport.period_end.desc(), StatementImport.id.desc())
            .all()
        )
        latest = next(
            (item for item in imports if item.closing_balance is not None), None
        )
        result.append(
            {
                **record_dict(account),
                "closing_balance": latest.closing_balance if latest else None,
                "balance_as_of": latest.period_end if latest else None,
                "imports": [record_dict(item) for item in imports],
            }
        )
    return result


@router.post("/bank-accounts", status_code=201)
def add_bank_account(
    data: BankAccountInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = BankAccount(user_id=user.id, **data.model_dump())
    db.add(row)
    commit(db)
    db.refresh(row)
    return record_dict(row)


@router.delete("/bank-accounts/{record_id}", status_code=204)
def delete_bank_account(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = owned(db, BankAccount, record_id, user)
    db.query(StatementEntry).filter_by(account_id=account.id).delete()
    db.query(StatementImport).filter_by(account_id=account.id).delete()
    db.delete(account)
    commit(db)


async def read_statement(file):
    content = await file.read(MAX_FILE_BYTES + 1)
    await file.close()
    try:
        return await run_in_threadpool(
            parse_statement, content, file.filename or "statement"
        )
    except StatementError as exc:
        raise HTTPException(422, str(exc)) from exc


def preview(db, account, parsed):
    other = (
        db.query(StatementImport)
        .join(BankAccount, BankAccount.id == StatementImport.account_id)
        .filter(
            BankAccount.user_id == account.user_id,
            StatementImport.account_id != account.id,
            StatementImport.file_hash == parsed["file_hash"],
        )
        .first()
    )
    if other:
        raise HTTPException(
            409,
            "This exact statement is already imported under another bank account. Use the original account to avoid counting it twice.",
        )
    references = {
        (row.transaction_date, row.reference, row.direction): row.amount
        for row in db.query(StatementEntry).filter_by(account_id=account.id).all()
        if row.reference
    }
    for row in parsed["rows"]:
        if row["reference"]:
            key = (row["transaction_date"], row["reference"], row["direction"])
            if key in references and references[key] != row["amount"]:
                raise HTTPException(
                    409,
                    "A transaction reference has conflicting amounts. Review the source statement before importing.",
                )
            references[key] = row["amount"]
    existing = {
        row[0]
        for row in db.query(StatementEntry.fingerprint)
        .filter_by(account_id=account.id)
        .all()
    }
    seen = set(existing)
    rows = []
    for i, row in enumerate(parsed["rows"]):
        duplicate = row["fingerprint"] in seen
        seen.add(row["fingerprint"])
        rows.append({**row, "row_index": i, "duplicate": duplicate})
    return {
        **{key: value for key, value in parsed.items() if key != "rows"},
        "rows": rows,
        "new_rows": sum(not row["duplicate"] for row in rows),
        "duplicate_rows": sum(row["duplicate"] for row in rows),
        "categories": CATEGORIES,
        "warnings": [
            "Review automatic categories, especially own-account transfers. Loan principal, interest and tenure require manual entry.",
            "Identical rows without a unique reference are treated as duplicates. Supply bank references to distinguish them.",
        ],
    }


@router.post("/statements/preview")
async def preview_statement(
    account_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = owned(db, BankAccount, account_id, user)
    return preview(db, account, await read_statement(file))


def persist_statement(db, account, parsed, filename, overrides=None):
    if (
        db.query(StatementImport)
        .filter_by(account_id=account.id, file_hash=parsed["file_hash"])
        .first()
    ):
        raise HTTPException(
            409, "This file has already been imported for this bank account."
        )
    reviewed = preview(db, account, parsed)
    if reviewed["new_rows"] == 0:
        raise HTTPException(
            409, "All transactions are already imported. Nothing was changed."
        )
    batch = StatementImport(
        account_id=account.id,
        filename=Path(filename).name[:200],
        **{
            key: parsed[key]
            for key in (
                "file_hash",
                "period_start",
                "period_end",
                "opening_balance",
                "closing_balance",
            )
        },
        imported_rows=reviewed["new_rows"],
        duplicate_rows=reviewed["duplicate_rows"],
    )
    db.add(batch)
    db.flush()
    for row in reviewed["rows"]:
        if row["duplicate"]:
            continue
        index = row["row_index"]
        data = {
            key: value
            for key, value in row.items()
            if key not in ("row_index", "duplicate")
        }
        data["category"] = (overrides or {}).get(str(index), data["category"])
        db.add(StatementEntry(account_id=account.id, import_id=batch.id, **data))
    return batch


@router.post("/statements/import", status_code=201)
async def import_statement(
    account_id: int = Form(...),
    categories: str = Form("{}"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = owned(db, BankAccount, account_id, user)
    parsed = await read_statement(file)
    try:
        overrides = json.loads(categories)
        if not isinstance(overrides, dict) or any(
            not isinstance(key, str)
            or not key.isdigit()
            or int(key) >= len(parsed["rows"])
            or value not in CATEGORIES
            for key, value in overrides.items()
        ):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "Invalid category review.")
    try:
        batch = persist_statement(
            db, account, parsed, file.filename or "statement", overrides
        )
        commit(db)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            409, "Statement was imported concurrently. Refresh and retry."
        ) from exc
    db.refresh(batch)
    return record_dict(batch)


@router.get("/sample-statement")
def sample_statement(format: str = "csv", user: User = Depends(get_current_user)):
    if format not in ("csv", "pdf"):
        raise HTTPException(422, "Choose csv or pdf.")
    path = SAMPLE_PATH.with_suffix("." + format)
    return FileResponse(
        path,
        media_type="text/csv" if format == "csv" else "application/pdf",
        filename=path.name,
    )


@router.post("/demo", status_code=201)
def load_demo(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Explicit opt-in only. Never silently overwrite a user's real financial profile.
    if (
        db.get(FinancialProfile, user.id)
        or db.query(BankAccount).filter_by(user_id=user.id).first()
        or db.query(Liability).filter_by(user_id=user.id).first()
    ):
        raise HTTPException(
            409,
            "Demo loading requires an empty financial profile. Download and import the sample instead.",
        )
    db.add(
        FinancialProfile(
            user_id=user.id,
            employer="Demo Software Studio",
            occupation="Software engineer",
            monthly_salary=90000,
            other_monthly_income=5000,
            monthly_expense_budget=65000,
            investment_value=420000,
            property_value=4200000,
            other_asset_value=150000,
            dependants=1,
        )
    )
    for data in (
        dict(
            name="Demo home mortgage",
            kind="MORTGAGE",
            lender="Example Housing Finance",
            original_amount=3000000,
            outstanding_amount=2450000,
            annual_interest_rate=8.5,
            monthly_payment=24500,
            remaining_months=174,
        ),
        dict(
            name="Demo education loan",
            kind="EDUCATION_LOAN",
            lender="Example Education Bank",
            original_amount=400000,
            outstanding_amount=180000,
            annual_interest_rate=9.5,
            monthly_payment=6500,
            remaining_months=32,
        ),
    ):
        db.add(Liability(user_id=user.id, as_of_date=date(2026, 9, 30), **data))
    account = BankAccount(
        user_id=user.id,
        name="Demo salary account",
        bank_name="Example Bank (fictional)",
        last_four="4821",
        currency="INR",
    )
    db.add(account)
    db.flush()
    parsed = parse_statement(SAMPLE_PATH.read_bytes(), SAMPLE_PATH.name)
    batch = persist_statement(db, account, parsed, SAMPLE_PATH.name)
    commit(db)
    return {
        "message": "Fictional six-month finances loaded.",
        "imported_rows": batch.imported_rows,
        "account_id": account.id,
    }
