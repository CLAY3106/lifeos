"""
Migration Tests — onboarding fields

Runs the add_onboarding_fields migration's upgrade()/downgrade() directly
against a throwaway SQLite engine, bound via alembic's Operations.context()
so the module's `op.*` calls work without going through `alembic upgrade`
(which would import app.database and its Postgres-only engine args).
"""

import importlib.util
import json
import pathlib
import uuid

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "alembic" / "versions" / "c3e5a7b9d1f4_add_onboarding_fields.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("add_onboarding_fields", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_adds_and_backfills_onboarding_columns():
    migration = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    metadata = sa.MetaData()
    # Pre-migration shape: just enough of `users` to exercise add_column
    # and the backfill UPDATE on an existing row.
    users = sa.Table("users", metadata, sa.Column("id", sa.String, primary_key=True))
    metadata.create_all(engine)

    existing_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(users.insert().values(id=existing_id))

    conn = engine.connect()
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        migration.upgrade()

    columns = {c["name"]: c for c in sa.inspect(engine).get_columns("users")}
    assert columns["onboarding_completed_at"]["nullable"] is True
    assert columns["active_modules"]["nullable"] is False

    row = conn.execute(
        sa.text("SELECT active_modules, onboarding_completed_at FROM users WHERE id = :id"),
        {"id": existing_id},
    ).fetchone()
    assert row[1] is None
    assert json.loads(row[0]) == ["academics", "jobs", "fitness", "finance"]

    with Operations.context(ctx):
        migration.downgrade()

    remaining = {c["name"] for c in sa.inspect(engine).get_columns("users")}
    assert "active_modules" not in remaining
    assert "onboarding_completed_at" not in remaining

    conn.close()
