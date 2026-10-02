import csv
import io
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-secret-key-never-use-in-production"
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import User, Account, Transaction
from app.models.financial import StatementEntry
from app.enums.account_type import AccountType
from app.enums.transaction_category import TransactionCategory
from app.enums.transaction_status import TransactionStatus
from app.services.statements import StatementError, parse_statement

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = (ROOT / "backend/data/sample-bank-statement.csv").read_bytes()
PROFILE = dict(
    employer="Example Studio",
    occupation="Designer",
    monthly_salary="90000",
    other_monthly_income="5000",
    monthly_expense_budget="65000",
    investment_value="420000",
    property_value="4200000",
    other_asset_value="150000",
    dependants=1,
)
LOAN = dict(
    name="Mortgage",
    kind="MORTGAGE",
    lender="Example Lender",
    original_amount="3000000",
    outstanding_amount="2450000",
    annual_interest_rate="8.5",
    monthly_payment="24500",
    remaining_months=174,
    as_of_date="2026-09-30",
)


@pytest.fixture
def context():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        users = [
            User(
                username=f"tester{i}",
                email=f"tester{i}@example.com",
                password_hash=hash_password("local-test-password"),
            )
            for i in (1, 2)
        ]
        db.add_all(users)
        db.commit()
        ids = [user.id for user in users]

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield (
            client,
            factory,
            [
                {"Authorization": f"Bearer {create_access_token(user_id)}"}
                for user_id in ids
            ],
        )
    app.dependency_overrides.clear()
    engine.dispose()


def bank(client, headers, name="Salary account"):
    response = client.post(
        "/financial/bank-accounts",
        headers=headers,
        json={"name": name, "bank_name": "Example Bank", "last_four": "4821"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def upload(
    client,
    headers,
    account_id,
    endpoint="preview",
    content=SAMPLE,
    filename="sample.csv",
    categories="{}",
):
    return client.post(
        f"/financial/statements/{endpoint}",
        headers=headers,
        data={"account_id": account_id, "categories": categories},
        files={"file": (filename, content, "application/octet-stream")},
    )


def test_sample_csv_and_pdf_are_equivalent():
    csv_data = parse_statement(SAMPLE, "sample.csv")
    pdf_data = parse_statement(
        (ROOT / "backend/data/sample-bank-statement.pdf").read_bytes(), "sample.pdf"
    )
    assert len(csv_data["rows"]) == 234
    assert csv_data["rows"] == pdf_data["rows"]
    assert csv_data["opening_balance"] == Decimal("125000")
    assert csv_data["closing_balance"] == Decimal("252374")


def test_preview_then_import_funds_linked_account_and_duplicate_protection(context):
    client, factory, headers = context
    account = bank(client, headers[0])
    with factory() as db:
        db.add(
            Account(
                owner_id=1,
                name="Spendable wallet",
                account_type=AccountType.PERSONAL,
                balance=5000,
                currency="INR",
            )
        )
        db.commit()
    response = upload(client, headers[0], account)
    assert response.status_code == 200, response.text
    assert response.json()["new_rows"] == 234
    assert (
        client.get("/financial/bank-accounts", headers=headers[0]).json()[0]["imports"]
        == []
    )
    response = upload(client, headers[0], account, "import", categories='{"1":"OTHER"}')
    assert response.status_code == 201, response.text
    assert response.json()["imported_rows"] == 234
    with factory() as db:
        assert db.query(Account).filter_by(name="Spendable wallet").one().balance == 5000
        assert db.query(Account).filter_by(name="Salary account").one().balance == 252374
        assert db.query(Transaction).count() == 0
        assert (
            db.query(StatementEntry).order_by(StatementEntry.id).all()[1].category
            == "OTHER"
        )
    assert upload(client, headers[0], account, "import").status_code == 409
    assert upload(client, headers[0], account).json()["duplicate_rows"] == 234
    pdf = (ROOT / "backend/data/sample-bank-statement.pdf").read_bytes()
    assert (
        upload(client, headers[0], account, "import", pdf, "same.pdf").status_code
        == 409
    )


def test_overlapping_import_only_adds_new_and_keeps_latest_balance(context):
    client, _, headers = context
    account = bank(client, headers[0])
    assert upload(client, headers[0], account, "import").status_code == 201
    all_rows = list(csv.reader(io.StringIO(SAMPLE.decode())))
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(all_rows[0])
    writer.writerows(all_rows[-2:])
    writer.writerow(
        ["2026-10-01", "New purchase", "100", "", "252274.00", "DEMO-NEW", "SHOPPING"]
    )
    response = upload(client, headers[0], account, "import", buffer.getvalue().encode())
    assert response.status_code == 201, response.text
    assert response.json()["imported_rows"] == 1
    assert response.json()["duplicate_rows"] == 2
    assert (
        Decimal(
            client.get("/financial/bank-accounts", headers=headers[0]).json()[0][
                "closing_balance"
            ]
        )
        == 252274
    )


def test_user_isolation_on_profile_liabilities_banks_and_import(context):
    client, _, headers = context
    assert (
        client.put("/financial/profile", headers=headers[0], json=PROFILE).status_code
        == 200
    )
    loan = client.post("/financial/liabilities", headers=headers[0], json=LOAN).json()
    account = bank(client, headers[0])
    assert upload(client, headers[1], account).status_code == 404
    assert upload(client, headers[1], account, "import").status_code == 404
    assert (
        client.put(
            f"/financial/liabilities/{loan['id']}", headers=headers[1], json=LOAN
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/financial/liabilities/{loan['id']}", headers=headers[1]
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/financial/bank-accounts/{account}", headers=headers[1]
        ).status_code
        == 404
    )
    assert (
        client.get("/financial/profile", headers=headers[1]).json()["profile"] is None
    )
    assert client.get("/financial/liabilities", headers=headers[1]).json() == []
    assert client.get("/financial/bank-accounts", headers=headers[1]).json() == []
    assert (
        client.get("/integration/financial-summary", headers=headers[1]).json()[
            "financial_twin"
        ]["metrics"]["total_outstanding_debt"]
        == 0
    )
    assert client.get("/financial/profile").status_code in (401, 403)


def test_demo_metrics_are_independently_reconciled(context):
    client, _, headers = context
    response = client.post("/financial/demo", headers=headers[0])
    assert response.status_code == 201, response.text
    twin = client.get("/integration/financial-summary", headers=headers[0]).json()[
        "financial_twin"
    ]
    m = twin["metrics"]
    data = list(csv.DictReader(io.StringIO(SAMPLE.decode())))
    income = sum(
        Decimal(row["Credit"] or 0) for row in data if row["Category"] != "TRANSFER"
    )
    expenses = sum(
        Decimal(row["Debit"] or 0)
        for row in data
        if row["Category"] not in ("TRANSFER", "INVESTMENT")
    )
    investments = sum(
        Decimal(row["Debit"] or 0) for row in data if row["Category"] == "INVESTMENT"
    )
    assert Decimal(str(m["observed_monthly_income"])) == round(income / 6, 2)
    assert Decimal(str(m["monthly_expenses"])) == round(expenses / 6, 2)
    assert Decimal(str(m["expense_to_income_percent"])) == round(
        expenses / income * 100, 2
    )
    assert Decimal(str(m["monthly_net_cash_flow"])) == round(
        (income - expenses - investments) / 6, 2
    )
    assert Decimal(str(m["debt_service_to_income_percent"])) == round(
        Decimal("31000") / Decimal("95000") * 100, 2
    )
    assert m["total_outstanding_debt"] == 2630000
    assert m["cash_balance"] == 252374
    assert m["estimated_net_worth"] == 2392374
    assert m["transaction_count"] == 234 and m["months_with_activity"] == 6
    assert (
        twin["period"]["start"] == "2026-04-01"
        and twin["period"]["end"] == "2026-09-30"
    )
    assert twin["analysis_source"] == "UNIFIED_BANK_LEDGER"
    assert len(twin["transactions"]) == 234
    assert client.post("/financial/demo", headers=headers[0]).status_code == 409
    assert (
        client.get(
            "/integration/financial-summary?months=3", headers=headers[0]
        ).json()["financial_twin"]["metrics"]["transaction_count"]
        == 117
    )
    assert (
        client.get(
            "/integration/financial-summary?months=0", headers=headers[0]
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/integration/financial-summary?end_date=2099-01-01", headers=headers[0]
        ).status_code
        == 422
    )


def test_zero_income_empty_months_and_missing_balances(context):
    client, _, headers = context
    twin = client.get("/integration/financial-summary", headers=headers[0]).json()[
        "financial_twin"
    ]
    assert twin["metrics"]["savings_rate_percent"] is None
    assert twin["metrics"]["expense_to_income_percent"] is None
    assert twin["metrics"]["cash_runway_months"] is None
    account = bank(client, headers[0])
    data = b"Date,Description,Debit,Credit\n2026-09-02,Purchase,100,\n"
    assert upload(client, headers[0], account, "import", data).status_code == 422
    twin = client.get("/integration/financial-summary", headers=headers[0]).json()[
        "financial_twin"
    ]
    assert len(twin["data_quality"]["missing_months"]) == 6
    assert twin["bank_accounts"][0]["balance"] == 0


def test_wallet_transfers_still_work_and_internal_failed_excluded(context):
    client, factory, headers = context
    with factory() as db:
        a = Account(
            owner_id=1,
            name="Personal",
            account_type=AccountType.PERSONAL,
            balance=5000,
            currency="INR",
        )
        b = Account(
            owner_id=2,
            name="Merchant",
            account_type=AccountType.PERSONAL,
            balance=0,
            currency="INR",
        )
        c = Account(
            owner_id=1,
            name="Second",
            account_type=AccountType.PERSONAL,
            balance=0,
            currency="INR",
        )
        db.add_all([a, b, c])
        db.commit()
        ids = [a.id, b.id, c.id]
    response = client.post(
        "/transactions/",
        headers=headers[0],
        json={
            "from_account_id": ids[0],
            "to_account_id": ids[1],
            "amount": 100,
            "category": "PURCHASE",
            "description": "Test payment",
        },
    )
    assert response.status_code == 200, response.text
    response = client.post(
        "/transactions/",
        headers=headers[0],
        json={
            "from_account_id": ids[0],
            "to_account_id": ids[2],
            "amount": 200,
            "category": "TRANSFER",
        },
    )
    assert response.status_code == 200, response.text
    with factory() as db:
        db.add(
            Transaction(
                from_account_id=ids[0],
                to_account_id=ids[1],
                amount=1000,
                category=TransactionCategory.PURCHASE,
                status=TransactionStatus.FAILED,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    summary = client.get(
        "/integration/financial-summary?months=1", headers=headers[0]
    ).json()
    assert summary["metrics"]["total_outflow"] == 100
    assert summary["financial_twin"]["metrics"]["monthly_expenses"] == 100
    assert len(summary["financial_twin"]["transactions"]) == 3


@pytest.mark.parametrize(
    "content",
    [
        b"Date,Description,Debit,Credit\n2026-09-01,Bad,100,100\n",
        b"Date,Description,Debit,Credit\n2026-09-01,Bad,-100,\n",
        b"Date,Description,Debit,Credit\n2099-09-01,Bad,100,\n",
        b"Date,Description,Debit,Credit,Balance\n2026-09-01,Bad,,100,200\n2026-09-02,Bad,100,,500\n",
        b"Date,Description,Debit,Credit\n2026-09-01,Bad,NaN,\n",
        b"Date,Description,Debit,Credit\n2026-09-01,Bad,1.001,\n",
        b"This is not a statement",
    ],
)
def test_invalid_statements_rejected_atomically(context, content):
    client, factory, headers = context
    account = bank(client, headers[0])
    assert upload(client, headers[0], account, "import", content).status_code == 422
    with factory() as db:
        assert db.query(StatementEntry).count() == 0


def test_profile_validation_liability_edit_and_delete_bank_data(context):
    client, factory, headers = context
    assert (
        client.put(
            "/financial/profile",
            headers=headers[0],
            json={**PROFILE, "monthly_salary": -1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/financial/liabilities",
            headers=headers[0],
            json={**LOAN, "annual_interest_rate": 101},
        ).status_code
        == 422
    )
    response = client.post("/financial/liabilities", headers=headers[0], json=LOAN)
    loan_id = response.json()["id"]
    assert (
        client.put(
            f"/financial/liabilities/{loan_id}",
            headers=headers[0],
            json={**LOAN, "outstanding_amount": 2400000},
        ).status_code
        == 200
    )
    assert (
        client.delete(
            f"/financial/liabilities/{loan_id}", headers=headers[0]
        ).status_code
        == 204
    )
    account = bank(client, headers[0])
    assert upload(client, headers[0], account, "import").status_code == 201
    assert (
        client.delete(
            f"/financial/bank-accounts/{account}", headers=headers[0]
        ).status_code
        == 409
    )
    with factory() as db:
        assert db.query(StatementEntry).count() == 234


def test_signup_login_and_sample_download(context):
    client, _, headers = context
    assert (
        client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "local-test-password",
            },
        ).status_code
        == 200
    )
    response = client.post(
        "/auth/login",
        json={"email": "newuser@example.com", "password": "local-test-password"},
    )
    assert response.status_code == 200
    assert (
        client.get("/financial/sample-statement", headers=headers[0]).content == SAMPLE
    )


def test_same_statement_cannot_be_counted_under_two_bank_accounts(context):
    client, _, headers = context
    first = bank(client, headers[0])
    second = bank(client, headers[0], name="Second account")
    assert upload(client, headers[0], first, "import").status_code == 201
    assert upload(client, headers[0], second).status_code == 409
    assert upload(client, headers[0], second, "import").status_code == 409


def test_reference_conflict_and_cosmetic_description_deduplication(context):
    client, _, headers = context
    account = bank(client, headers[0])
    original = (
        b"Date,Description,Debit,Credit,Balance,Reference\n2026-09-01,Purchase,100,,900,REF-1\n"
    )
    changed = b"Date,Description,Debit,Credit,Balance,Reference\n2026-09-01,Purchase revised,101,,899,REF-1\n"
    cosmetic = b"Date,Description,Debit,Credit,Balance,Reference\n2026-09-01,Purchase revised,100,,900,REF-1\n"
    assert upload(client, headers[0], account, "import", original).status_code == 201
    assert upload(client, headers[0], account, "import", changed).status_code == 409
    assert upload(client, headers[0], account, "import", cosmetic).status_code == 409


def test_day_first_aliases_and_descending_statements():
    data = b"Transaction Date,Narration,Withdrawal,Deposit,Running Balance,Ref No\n02/09/2026,Shop,25,,175,B\n01/09/2026,Payroll,,100,200,A\n"
    parsed = parse_statement(data, "bank.csv")
    assert parsed["opening_balance"] == 100
    assert parsed["closing_balance"] == 175
    assert parsed["rows"][0]["transaction_date"] == date(2026, 9, 1)
    assert parsed["rows"][0]["category"] == "SALARY"
