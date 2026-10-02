"""One account balance and statement history, composed of imports and live transfers."""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import or_

from app.models.account import Account
from app.models.financial import BankAccount, StatementEntry
from app.models.transaction import Transaction
from app.enums.account_type import AccountType
from app.enums.transaction_status import TransactionStatus

ZERO = Decimal("0")


def linked_account(db, bank, lock=False):
    query = db.query(Account).filter(
        Account.id == bank.wallet_account_id,
        Account.owner_id == bank.user_id,
        Account.is_system.is_(False),
        Account.currency == "INR",
    )
    if lock:
        query = query.with_for_update().populate_existing()
    account = query.first()
    if account is None:
        raise HTTPException(409, "Bank account is not linked to a valid INR account.")
    return account


def attach_account(db, bank, wallet_id=None):
    if wallet_id is not None:
        account = db.query(Account).filter_by(
            id=wallet_id, owner_id=bank.user_id, is_system=False, currency="INR"
        ).first()
        if account is None:
            raise HTTPException(404, "Your INR account was not found.")
        if db.query(BankAccount).filter_by(wallet_account_id=wallet_id).first():
            raise HTTPException(409, "This account already has statement history. Use its existing bank account.")
    else:
        account = Account(
            owner_id=bank.user_id, name=bank.name, account_type=AccountType.PERSONAL,
            balance=ZERO, currency="INR", is_system=False,
        )
        db.add(account)
        db.flush()
    bank.wallet_account_id = account.id
    return account


def live_rows(db, account):
    transactions = db.query(Transaction).filter(
        or_(Transaction.from_account_id == account.id, Transaction.to_account_id == account.id),
        Transaction.status == TransactionStatus.SUCCESS,
    ).order_by(Transaction.created_at, Transaction.id).all()
    rows = []
    for txn in transactions:
        outgoing = txn.from_account_id == account.id
        internal = txn.from_account.owner_id == txn.to_account.owner_id
        rows.append({
            "id": txn.id, "date": txn.created_at.date(),
            "description": txn.description or txn.category.value,
            "direction": "OUTFLOW" if outgoing else "INFLOW", "amount": txn.amount,
            "category": "TRANSFER" if internal else ("OTHER" if txn.category.value == "TRANSFER" else txn.category.value),
            "original_category": txn.category.value,
            "reference": f"WALLET-{txn.id}", "source": "TRANSFER",
            "account_id": account.id, "recorded_balance": None,
            "sort_order": (txn.created_at.date(), 1, txn.id),
        })
    return rows


def entry_row(entry, account_id, order):
    get = entry.get if isinstance(entry, dict) else lambda key: getattr(entry, key)
    return {
        "id": order, "date": get("transaction_date"), "description": get("description"),
        "direction": get("direction"), "amount": get("amount"),
        "category": get("category"), "reference": get("reference"),
        "source": "STATEMENT_IMPORT", "account_id": account_id,
        "recorded_balance": get("balance"), "sort_order": (get("transaction_date"), 0, order),
    }


def signed(row):
    return row["amount"] if row["direction"] == "INFLOW" else -row["amount"]


def account_ledger(db, account, bank=None, extra_entries=(), validate=False):
    bank = bank or db.query(BankAccount).filter_by(wallet_account_id=account.id).first()
    entries = db.query(StatementEntry).filter_by(account_id=bank.id).order_by(
        StatementEntry.transaction_date, StatementEntry.id
    ).all() if bank else []
    rows = [entry_row(entry, account.id, entry.id) for entry in entries]
    next_order = max((entry.id for entry in entries), default=0) + 1
    rows += [entry_row(entry, account.id, next_order + i) for i, entry in enumerate(extra_entries)]
    rows += live_rows(db, account)
    rows.sort(key=lambda row: row["sort_order"])
    anchor = next((i for i, row in enumerate(rows) if row["recorded_balance"] is not None), None)
    if anchor is None:
        opening = account.balance - sum((signed(row) for row in rows), ZERO)
    else:
        opening = rows[anchor]["recorded_balance"] - sum((signed(row) for row in rows[:anchor + 1]), ZERO)
    running = opening
    for row in rows:
        running += signed(row)
        if validate and row["recorded_balance"] is not None and running != row["recorded_balance"]:
            raise HTTPException(409, "Statement history does not reconcile with this account. Upload the missing history or correct overlapping balances; no changes were saved.")
        row["balance"] = running
        row.pop("recorded_balance")
        row.pop("sort_order")
    return {"account_id": account.id, "account_name": account.name, "currency": account.currency,
            "opening_balance": opening, "closing_balance": running, "transactions": rows}


def import_effect(db, bank, reviewed, parsed):
    account = linked_account(db, bank, lock=True)
    if parsed["closing_balance"] is None:
        raise HTTPException(422, "Include a running Balance for every row so the imported bank balance can be established safely.")
    live = live_rows(db, account)
    matched = set()
    by_ref = {row["reference"]: row for row in live}
    for row in reviewed["rows"]:
        ref = row["reference"]
        if ref.startswith("WALLET-"):
            existing = by_ref.get(ref)
            if not existing or (row["transaction_date"], row["direction"], row["amount"]) != (
                existing["date"], existing["direction"], existing["amount"]
            ):
                raise HTTPException(409, "A Persona Wallet reference does not match this account's transfer.")
            row["duplicate"] = True
            matched.add(ref)
    # A statement must not silently absorb a payment already posted by this app.
    prior_end = max((row.transaction_date for row in db.query(StatementEntry).filter_by(account_id=bank.id)), default=None)
    for row in live:
        if (prior_end is None or row["date"] > prior_end) and row["date"] <= parsed["period_end"] and row["reference"] not in matched:
            raise HTTPException(409, "This statement overlaps live Persona Wallet transfers. Use a statement ending before those transfers, or the exported account statement containing their WALLET references.")
    new = [row for row in reviewed["rows"] if not row["duplicate"]]
    ledger = account_ledger(db, account, bank, new, validate=True)
    if ledger["closing_balance"] < 0:
        raise HTTPException(409, "The imported balance cannot cover transfers already posted to this account.")
    if ledger["closing_balance"] >= Decimal("10000000000000"):
        raise HTTPException(422, "Account balance exceeds the supported amount.")
    return account, ledger["closing_balance"]
