import uuid
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Set JWT_SECRET before importing app
os.environ.setdefault("JWT_SECRET", "test-secret-for-testing-only")

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.services.auth import hash_password, create_access_token

# Monkey-patch PostgreSQL UUID type to render as TEXT for SQLite
@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def demo_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="test@lifeos.app",
        hashed_password=hash_password("test1234"),
        name="Test User",
        monthly_budget=300,
        weekly_capacity_hours=40,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(demo_user):
    token = create_access_token({"sub": str(demo_user.id)})
    return {"cookies": {"access_token": token}}
