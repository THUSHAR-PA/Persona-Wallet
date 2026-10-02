"""Run both directions on an isolated SQLite DB and compare ORM schema to migrations."""

import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import create_engine, inspect

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
    command.downgrade(config, "baff1681361d")
    assert "statement_entries" not in inspect(engine).get_table_names()
    assert "users" in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
print("Migration upgrade, downgrade, re-upgrade and ORM parity verified.")
