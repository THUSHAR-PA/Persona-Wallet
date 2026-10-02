"""Transparent arithmetic for PersonaTwin, with source and observation dates."""

from calendar import monthrange
from datetime import date
from decimal import Decimal

from app.models.financial import (
    BankAccount,
    FinancialProfile,
    Liability,
    StatementEntry,
    StatementImport,
)

ZERO = Decimal("0")


def serialize(record):
    return {
        column.name: getattr(record, column.name) for column in record.__table__.columns
    }


def month_start(end, offset):
    index = end.year * 12 + end.month - 1 - offset
    return date(index // 12, index % 12 + 1, 1)


def ratio(numerator, denominator):
    return round(numerator / denominator * 100, 2) if denominator > 0 else None


def financial_analysis(
    db, user, wallet_accounts, wallet_transactions, months=6, requested_end=None
):
    profile = db.get(FinancialProfile, user.id)
    liabilities = (
        db.query(Liability).filter_by(user_id=user.id).order_by(Liability.id).all()
    )
    bank_accounts = (
        db.query(BankAccount).filter_by(user_id=user.id).order_by(BankAccount.id).all()
    )
    account_ids = [account.id for account in bank_accounts]
    entries = (
        db.query(StatementEntry)
        .filter(StatementEntry.account_id.in_(account_ids))
        .order_by(StatementEntry.transaction_date, StatementEntry.id)
        .all()
        if account_ids
        else []
    )
    imports = (
        db.query(StatementImport)
        .filter(StatementImport.account_id.in_(account_ids))
        .order_by(StatementImport.period_end.desc(), StatementImport.id.desc())
        .all()
        if account_ids
        else []
    )
    # Prefer bank observations, rather than counting simulated wallet transfers again.
    source = "BANK_STATEMENTS" if entries else "WALLET_LEDGER"
    observations = []
    if entries:
        for entry in entries:
            observations.append(
                {
                    "id": entry.id,
                    "date": entry.transaction_date,
                    "description": entry.description,
                    "amount": entry.amount,
                    "direction": entry.direction,
                    "category": entry.category,
                    "account_id": entry.account_id,
                    "reference": entry.reference,
                }
            )
    else:
        for txn in wallet_transactions:
            if txn.status.value != "SUCCESS":
                continue
            from_user = txn.from_account.owner_id == user.id
            to_user = txn.to_account.owner_id == user.id
            if from_user == to_user:
                continue
            owned_account = txn.from_account if from_user else txn.to_account
            if owned_account.currency != "INR":
                continue
            observations.append(
                {
                    "id": txn.id,
                    "date": txn.created_at.date(),
                    "description": txn.description or txn.category.value,
                    "amount": txn.amount,
                    "direction": "OUTFLOW" if from_user else "INFLOW",
                    "category": txn.category.value,
                    "account_id": owned_account.id,
                    "reference": "",
                }
            )
    end = requested_end or max(
        (row["date"] for row in observations), default=date.today()
    )
    start = month_start(end, months - 1)
    selected = [row for row in observations if start <= row["date"] <= end]
    buckets = {
        month_start(end, offset).strftime("%Y-%m"): {
            "month": month_start(end, offset).strftime("%Y-%m"),
            "income": ZERO,
            "salary": ZERO,
            "expenses": ZERO,
            "emi_paid": ZERO,
            "investments": ZERO,
            "transaction_count": 0,
        }
        for offset in reversed(range(months))
    }
    category_spend = {}
    for row in selected:
        bucket = buckets[row["date"].strftime("%Y-%m")]
        bucket["transaction_count"] += 1
        if row["category"] == "TRANSFER":
            continue
        if row["direction"] == "INFLOW":
            bucket["income"] += row["amount"]
            if row["category"] == "SALARY":
                bucket["salary"] += row["amount"]
        elif row["category"] == "INVESTMENT":
            bucket["investments"] += row["amount"]
        else:
            bucket["expenses"] += row["amount"]
            category_spend[row["category"]] = (
                category_spend.get(row["category"], ZERO) + row["amount"]
            )
            if row["category"] == "EMI":
                bucket["emi_paid"] += row["amount"]
    for bucket in buckets.values():
        bucket["surplus_before_investments"] = bucket["income"] - bucket["expenses"]
        bucket["net_cash_flow"] = (
            bucket["income"] - bucket["expenses"] - bucket["investments"]
        )
        bucket["expense_to_income_percent"] = ratio(
            bucket["expenses"], bucket["income"]
        )
    total = {
        key: sum((bucket[key] for bucket in buckets.values()), ZERO)
        for key in (
            "income",
            "salary",
            "expenses",
            "emi_paid",
            "investments",
            "net_cash_flow",
        )
    }
    average = {key: round(value / months, 2) for key, value in total.items()}
    declared_income = (
        (profile.monthly_salary + profile.other_monthly_income) if profile else ZERO
    )
    monthly_payments = sum((loan.monthly_payment for loan in liabilities), ZERO)
    debt = sum((loan.outstanding_amount for loan in liabilities), ZERO)
    banks = []
    for account in bank_accounts:
        latest = next(
            (
                batch
                for batch in imports
                if batch.account_id == account.id
                and batch.period_end <= end
                and batch.closing_balance is not None
            ),
            None,
        )
        banks.append(
            {
                **serialize(account),
                "balance": latest.closing_balance if latest else None,
                "balance_as_of": latest.period_end if latest else None,
            }
        )
    cash = (
        sum((bank["balance"] for bank in banks if bank["balance"] is not None), ZERO)
        if entries
        else sum(
            (
                account.balance
                for account in wallet_accounts
                if account.currency == "INR" and not account.is_system
            ),
            ZERO,
        )
    )
    other_assets = (
        (profile.investment_value + profile.property_value + profile.other_asset_value)
        if profile
        else ZERO
    )
    flags = []
    if not selected:
        flags.append("No transactions in this observation window.")
    missing_months = [
        bucket["month"]
        for bucket in buckets.values()
        if not bucket["transaction_count"]
    ]
    if missing_months:
        flags.append(
            "No recorded transactions for: "
            + ", ".join(missing_months)
            + ". Monthly averages still include these months."
        )
    if end.day != monthrange(end.year, end.month)[1]:
        flags.append(
            "The final month is partial; monthly ratios may change with additional transactions."
        )
    if entries:
        flags.append(
            "Bank statement analytics exclude wallet transfers to avoid adding the same money twice."
        )
    else:
        flags.append(
            "Only the wallet ledger is available. Upload statements to observe external banking activity."
        )
    if banks and any(bank["balance"] is None for bank in banks):
        flags.append(
            "Some bank accounts have no reconciled closing balance; cash and net worth are incomplete."
        )
    if any(
        bank["balance_as_of"] and (end - bank["balance_as_of"]).days > 31
        for bank in banks
    ):
        flags.append(
            "Some bank balance snapshots are more than 31 days older than the analysis end date."
        )
    if liabilities:
        flags.append(
            "Debt balances and EMI schedules are self-reported; statement EMIs do not automatically reduce principal."
        )
    flags.append(
        "Own-account transfers must be classified as TRANSFER in every imported account to avoid overstating income and spending."
    )
    return {
        "schema_version": "2.0",
        "currency": "INR",
        "analysis_source": source,
        "period": {
            "start": start,
            "end": end,
            "months": months,
            "averages_denominator_months": months,
        },
        "profile": serialize(profile) if profile else None,
        "liabilities": [serialize(loan) for loan in liabilities],
        "bank_accounts": banks,
        "metrics": {
            "declared_monthly_income": declared_income,
            "observed_monthly_income": average["income"],
            "observed_monthly_salary": average["salary"],
            "monthly_expenses": average["expenses"],
            "monthly_investments": average["investments"],
            "observed_monthly_emi": average["emi_paid"],
            "monthly_surplus_before_investments": average["income"]
            - average["expenses"],
            "monthly_net_cash_flow": average["net_cash_flow"],
            "expense_to_income_percent": ratio(total["expenses"], total["income"]),
            "savings_rate_percent": ratio(
                total["income"] - total["expenses"], total["income"]
            ),
            "declared_monthly_emi": monthly_payments,
            "total_outstanding_debt": debt,
            "mortgage_outstanding": sum(
                (
                    loan.outstanding_amount
                    for loan in liabilities
                    if loan.kind == "MORTGAGE"
                ),
                ZERO,
            ),
            "debt_service_to_income_percent": ratio(monthly_payments, declared_income),
            "cash_balance": cash,
            "reported_assets": cash + other_assets,
            "estimated_net_worth": cash + other_assets - debt,
            "cash_runway_months": round(max(cash, ZERO) / average["expenses"], 2)
            if average["expenses"] > 0
            else None,
            "budget_variance": profile.monthly_expense_budget - average["expenses"]
            if profile and profile.monthly_expense_budget > 0
            else None,
            "transaction_count": len(selected),
            "months_with_activity": months - len(missing_months),
        },
        "monthly_cash_flow": list(buckets.values()),
        "category_spend": [
            {"category": key, "amount": value}
            for key, value in sorted(
                category_spend.items(), key=lambda item: item[1], reverse=True
            )
        ],
        "statement_imports": [serialize(batch) for batch in imports],
        "recent_transactions": sorted(
            selected, key=lambda row: (row["date"], row["id"]), reverse=True
        )[:10],
        "transactions": selected,
        "data_quality": {
            "flags": flags,
            "profile_present": profile is not None,
            "statement_count": len(imports),
            "missing_months": missing_months,
            "salary_identified": total["salary"] > 0,
            "loan_details_source": "SELF_REPORTED",
            "category_source": "HEURISTIC_OR_USER_REVIEWED",
        },
        "definitions": {
            "expense_to_income_percent": "Non-investment outflows / observed inflows * 100; excludes TRANSFER.",
            "savings_rate_percent": "(Observed income - expenses) / observed income * 100; before investments.",
            "debt_service_to_income_percent": "Self-reported monthly debt payments / declared monthly income * 100.",
            "estimated_net_worth": "Latest available bank cash snapshots (or INR wallet balances when no statements), plus declared assets, minus declared debt. These are current snapshots, not historical valuations.",
            "cash_runway_months": "Non-negative observed cash / average monthly expenses; expenses include EMIs.",
            "budget_variance": "Declared monthly expense budget minus observed monthly expenses; includes EMIs, excludes investments.",
        },
    }
