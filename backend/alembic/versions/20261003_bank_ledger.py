"""Link imported bank history to spendable accounts, preserving existing demo data."""
from alembic import op
import sqlalchemy as sa

revision = "20261003_bank_ledger"
down_revision = "20261002_financial_profile"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("statement_accounts") as batch:
        batch.add_column(sa.Column("wallet_account_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_statement_wallet_account", "accounts", ["wallet_account_id"], ["id"])
        batch.create_unique_constraint("uq_statement_wallet_account", ["wallet_account_id"])
    # Each existing imported account becomes its own account. Existing wallet
    # accounts/transfers are never overwritten. Latest known closing balance funds it.
    op.execute("""
        INSERT INTO accounts (owner_id, name, account_type, balance, currency, is_system, created_at)
        SELECT s.user_id, 'Imported bank ' || s.id || ': ' || substr(s.name, 1, 70),
               'PERSONAL', COALESCE((SELECT i.closing_balance FROM statement_imports i
                 WHERE i.account_id = s.id AND i.closing_balance IS NOT NULL
                 ORDER BY i.period_end DESC, i.id DESC LIMIT 1), 0), s.currency, false, CURRENT_TIMESTAMP
        FROM statement_accounts s WHERE s.wallet_account_id IS NULL
    """)
    op.execute("""
        UPDATE statement_accounts SET wallet_account_id = (
          SELECT MAX(a.id) FROM accounts a WHERE a.owner_id = statement_accounts.user_id
          AND a.name = 'Imported bank ' || statement_accounts.id || ': ' || substr(statement_accounts.name, 1, 70)
        ) WHERE wallet_account_id IS NULL
    """)


def downgrade():
    # Keep generated accounts/balances; never destroy funded accounts on rollback.
    with op.batch_alter_table("statement_accounts") as batch:
        batch.drop_constraint("uq_statement_wallet_account", type_="unique")
        batch.drop_constraint("fk_statement_wallet_account", type_="foreignkey")
        batch.drop_column("wallet_account_id")
