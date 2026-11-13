"""
Seed Tests — demo user onboarding

seed() opens its own session via app.seed.SessionLocal rather than the
get_db dependency, so these tests monkeypatch it to a session bound to
the same transactional connection as db_session, keeping every insert
inside the fixture's rollback.
"""
import conftest

import app.seed as seed_module
from app.models.user import User


def _bind_seed_to_test_connection(monkeypatch, db_session):
    connection = db_session.get_bind()
    monkeypatch.setattr(
        seed_module, "SessionLocal", lambda: conftest.TestingSessionLocal(bind=connection)
    )


def test_seed_creates_demo_user_already_onboarded(monkeypatch, db_session):
    _bind_seed_to_test_connection(monkeypatch, db_session)

    seed_module.seed()

    demo = db_session.query(User).filter(User.email == "demo@lifeos.app").first()
    assert demo is not None
    assert demo.onboarding_completed_at is not None
    assert set(demo.active_modules) == {"academics", "jobs", "fitness", "finance"}


def test_seed_backfills_onboarding_for_pre_onboarding_demo_account(monkeypatch, db_session, demo_user):
    # Simulate a demo account seeded before onboarding existed: same email
    # the real seeder looks for, but no completion timestamp.
    demo_user.email = "demo@lifeos.app"
    demo_user.onboarding_completed_at = None
    db_session.commit()

    _bind_seed_to_test_connection(monkeypatch, db_session)
    seed_module.seed()

    db_session.refresh(demo_user)
    assert demo_user.onboarding_completed_at is not None
