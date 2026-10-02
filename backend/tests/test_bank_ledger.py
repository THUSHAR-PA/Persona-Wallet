from datetime import date
from decimal import Decimal

from test_financial import context, bank, upload, SAMPLE
from app.models.account import Account
from app.models.financial import BankAccount, StatementEntry
from app.enums.account_type import AccountType
from app.services.statements import parse_statement


def accounts(client, headers):
    return client.get("/accounts/", headers=headers).json()


def transfer(client, headers, source, destination, amount=5000, category="TRANSFER"):
    response = client.post("/transactions/", headers=headers, json={
        "from_account_id": source, "to_account_id": destination,
        "amount": amount, "category": category, "description": "Bank payment",
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_demo_transfer_updates_both_accounts_statements_and_analysis(context):
    client, factory, headers = context
    demo = client.post("/financial/demo", headers=headers[0])
    assert demo.status_code == 201, demo.text
    source = accounts(client, headers[0])[0]["id"]
    with factory() as db:
        recipient = Account(owner_id=2, name="Recipient", account_type=AccountType.PERSONAL,
                            balance=0, currency="INR", is_system=False)
        db.add(recipient); db.commit(); destination = recipient.id
    txn = transfer(client, headers[0], source, destination)
    assert Decimal(accounts(client, headers[0])[0]["balance"]) == 247374
    assert Decimal(accounts(client, headers[1])[0]["balance"]) == 5000
    statement = client.get(f"/accounts/{source}/statement", headers=headers[0]).json()
    assert len(statement["transactions"]) == 235
    assert statement["closing_balance"] == 247374
    assert statement["transactions"][-1]["balance"] == 247374
    assert statement["transactions"][-1]["reference"] == f"WALLET-{txn['id']}"
    received = client.get(f"/accounts/{destination}/statement", headers=headers[1]).json()
    assert received["transactions"][0]["direction"] == "INFLOW"
    twin = client.get("/integration/financial-summary?months=1", headers=headers[0]).json()["financial_twin"]
    assert twin["metrics"]["cash_balance"] == 247374
    assert twin["metrics"]["monthly_expenses"] == 5000
    assert twin["metrics"]["total_outstanding_debt"] == 2630000
    assert len(twin["account_statements"][0]["transactions"]) == 235
    assert client.get(f"/accounts/{source}/statement", headers=headers[1]).status_code == 404


def test_export_roundtrip_and_old_upload_never_reset_new_transfer(context):
    client, factory, headers = context
    bank_id = bank(client, headers[0])
    assert upload(client, headers[0], bank_id, "import").status_code == 201
    source = accounts(client, headers[0])[0]["id"]
    with factory() as db:
        recipient = Account(owner_id=2, name="Recipient", account_type=AccountType.PERSONAL,
                            balance=0, currency="INR", is_system=False)
        db.add(recipient); db.commit(); destination = recipient.id
    transfer(client, headers[0], source, destination)
    exported = client.get(f"/financial/bank-accounts/{bank_id}/statement?format=csv", headers=headers[0])
    parsed = parse_statement(exported.content, "export.csv")
    assert len(parsed["rows"]) == 235
    assert parsed["closing_balance"] == Decimal("247374")
    preview = upload(client, headers[0], bank_id, content=exported.content)
    assert preview.status_code == 200, preview.text
    assert preview.json()["duplicate_rows"] == 235
    assert upload(client, headers[0], bank_id, "import", exported.content).status_code == 409
    assert upload(client, headers[0], bank_id, "import").status_code == 409
    assert Decimal(accounts(client, headers[0])[0]["balance"]) == 247374
    with factory() as db:
        assert db.query(StatementEntry).count() == 234


def test_historical_backfill_and_next_statement_preserve_posted_transfers(context):
    client, factory, headers = context
    bank_id = bank(client, headers[0])
    assert upload(client, headers[0], bank_id, "import").status_code == 201
    older = b"Date,Description,Debit,Credit,Balance,Reference,Category\n2026-03-31,Earlier salary,,1000,125000,OLDER,SALARY\n"
    assert upload(client, headers[0], bank_id, "import", older).status_code == 201
    assert Decimal(accounts(client, headers[0])[0]["balance"]) == 252374
    with factory() as db:
        recipient = Account(owner_id=2, name="Recipient", account_type=AccountType.PERSONAL,
                            balance=0, currency="INR", is_system=False)
        db.add(recipient); db.commit(); destination = recipient.id
    source = accounts(client, headers[0])[0]["id"]
    transfer(client, headers[0], source, destination)
    following = b"Date,Description,Debit,Credit,Balance,Reference,Category\n2026-10-01,Groceries,100,,252274,NEXT,GROCERIES\n"
    result = upload(client, headers[0], bank_id, "import", following)
    assert result.status_code == 201, result.text
    assert Decimal(accounts(client, headers[0])[0]["balance"]) == 247274
    bad = b"Date,Description,Debit,Credit,Balance,Reference,Category\n2026-03-30,Conflicting credit,,1,500,BAD,OTHER\n"
    assert upload(client, headers[0], bank_id, "import", bad).status_code == 409
    assert Decimal(accounts(client, headers[0])[0]["balance"]) == 247274


def test_link_existing_account_and_reject_foreign_or_double_link(context):
    client, factory, headers = context
    with factory() as db:
        a = Account(owner_id=1, name="Existing", account_type=AccountType.PERSONAL,
                    balance=5000, currency="INR", is_system=False)
        db.add(a); db.commit(); wallet_id = a.id
    data = {"name": "Main bank", "bank_name": "Example Bank", "wallet_account_id": wallet_id}
    assert client.post("/financial/bank-accounts", headers=headers[1], json=data).status_code == 404
    result = client.post("/financial/bank-accounts", headers=headers[0], json=data)
    assert result.status_code == 201, result.text
    assert upload(client, headers[0], result.json()["id"], "import").status_code == 201
    assert len(accounts(client, headers[0])) == 1
    assert Decimal(accounts(client, headers[0])[0]["balance"]) == 252374
    assert client.post("/financial/bank-accounts", headers=headers[0], json={**data, "name": "Duplicate"}).status_code == 409


def test_overlapping_live_payment_cannot_be_imported_twice(context):
    client, factory, headers = context
    bank_id = bank(client, headers[0])
    assert upload(client, headers[0], bank_id, "import").status_code == 201
    source = accounts(client, headers[0])[0]["id"]
    with factory() as db:
        a = Account(owner_id=2, name="Recipient", account_type=AccountType.PERSONAL,
                    balance=0, currency="INR", is_system=False)
        db.add(a); db.commit(); destination = a.id
    transfer(client, headers[0], source, destination)
    data = f"Date,Description,Debit,Credit,Balance,Reference\n{date.today()},Payment,5000,,247374,UNMATCHED\n".encode()
    response = upload(client, headers[0], bank_id, "import", data)
    assert response.status_code == 409, response.text
    assert Decimal(accounts(client, headers[0])[0]["balance"]) == 247374
