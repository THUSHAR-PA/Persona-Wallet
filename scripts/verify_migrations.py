"""Run both directions on an isolated SQLite DB and compare ORM schema to migrations."""

import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import create_engine, inspect, text

with tempfile.TemporaryDirectory() as directory:
    os.environ["DATABASE_URL"] = f"sqlite:///{directory}/migrations.db"
    os.chdir(Path(__file__).resolve().parents[1] / "backend")
    from app.core.database import Base
    import app.models

    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as connection:
        differences = compare_metadata(
            MigrationContext.configure(connection), Base.metadata
        )
    assert not differences, differences
    assert "statement_entries" in inspect(engine).get_table_names()
    # Exercise the migration against an existing imported/demo account, not just
    # empty tables. The previous standalone wallet balance must be preserved.
    command.downgrade(config, "20261002_financial_profile")
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id,username,email,password_hash,created_at) VALUES (1,'migration-demo','migration@example.com','fixture',CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO accounts (id,owner_id,name,account_type,balance,currency,is_system,created_at) VALUES (1,1,'Existing wallet','PERSONAL',500,'INR',false,CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO statement_accounts (id,user_id,name,bank_name,last_four,currency) VALUES (1,1,'Imported demo','Example','4821','INR')"))
        connection.execute(text("INSERT INTO statement_imports (id,account_id,filename,file_hash,period_start,period_end,opening_balance,closing_balance,imported_rows,duplicate_rows,created_at) VALUES (1,1,'fixture.csv','fixture','2026-09-01','2026-09-01',100,120,1,0,CURRENT_TIMESTAMP)"))
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT balance FROM accounts WHERE id=1")).scalar() == 500
        assert connection.execute(text("SELECT a.balance FROM accounts a JOIN statement_accounts s ON s.wallet_account_id=a.id WHERE s.id=1")).scalar() == 120
        assert connection.execute(text("SELECT COUNT(*) FROM statement_imports")).scalar() == 1
    command.downgrade(config, "baff1681361d")
    assert "statement_entries" not in inspect(engine).get_table_names()
    assert "users" in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
print("Migration upgrade, downgrade, re-upgrade and ORM parity verified.")
