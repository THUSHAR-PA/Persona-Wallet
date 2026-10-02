"""Add financial profiles, debt, and statement observations without changing wallet balances."""

from alembic import op
import sqlalchemy as sa

revision = "20261002_financial_profile"
down_revision = "baff1681361d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "financial_profiles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("employer", sa.String(120), nullable=False),
        sa.Column("occupation", sa.String(120), nullable=False),
        *[
            sa.Column(name, sa.Numeric(15, 2), nullable=False)
            for name in (
                "monthly_salary",
                "other_monthly_income",
                "monthly_expense_budget",
                "investment_value",
                "property_value",
                "other_asset_value",
            )
        ],
        sa.Column("dependants", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_table(
        "financial_liabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("lender", sa.String(120), nullable=False),
        *[
            sa.Column(name, sa.Numeric(15, 2), nullable=False)
            for name in ("original_amount", "outstanding_amount", "monthly_payment")
        ],
        sa.Column("annual_interest_rate", sa.Numeric(6, 3), nullable=False),
        sa.Column("remaining_months", sa.Integer(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
    )
    op.create_index(
        "ix_financial_liabilities_user_id", "financial_liabilities", ["user_id"]
    )
    op.create_table(
        "statement_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("bank_name", sa.String(120), nullable=False),
        sa.Column("last_four", sa.String(4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_statement_account_name"),
    )
    op.create_index("ix_statement_accounts_user_id", "statement_accounts", ["user_id"])
    op.create_table(
        "statement_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("statement_accounts.id"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("opening_balance", sa.Numeric(15, 2)),
        sa.Column("closing_balance", sa.Numeric(15, 2)),
        sa.Column("imported_rows", sa.Integer(), nullable=False),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.UniqueConstraint("account_id", "file_hash", name="uq_statement_file"),
    )
    op.create_index(
        "ix_statement_imports_account_id", "statement_imports", ["account_id"]
    )
    op.create_table(
        "statement_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("statement_accounts.id"),
            nullable=False,
        ),
        sa.Column(
            "import_id",
            sa.Integer(),
            sa.ForeignKey("statement_imports.id"),
            nullable=False,
        ),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("reference", sa.String(120), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("balance", sa.Numeric(15, 2)),
        sa.UniqueConstraint("account_id", "fingerprint", name="uq_statement_entry"),
    )
    op.create_index(
        "ix_statement_entries_account_id", "statement_entries", ["account_id"]
    )
    op.create_index(
        "ix_statement_entries_transaction_date",
        "statement_entries",
        ["transaction_date"],
    )


def downgrade():
    for table in (
        "statement_entries",
        "statement_imports",
        "statement_accounts",
        "financial_liabilities",
        "financial_profiles",
    ):
        op.drop_table(table)
