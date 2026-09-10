"""
Database — SQLAlchemy Engine, Session, and Base

This module provides the database connection and session management:
1. Engine — Connection pool with health checks
2. SessionLocal — Session factory for database operations
3. Base — Declarative base for all models
4. get_db — Dependency injection for database sessions
5. check_db_connection — Health check endpoint

The database uses PostgreSQL with connection pooling:
- pool_pre_ping: Checks connections before use (prevents stale connections)
- pool_recycle: Recycles connections after 300 seconds (prevents timeout)
- pool_timeout: Times out after 10 seconds if no connections available
- connect_timeout: Times out after 10 seconds if can't connect
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment variable (defaults to local PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/lifeos")

# Create engine with connection pooling and health checks
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Check connections before use (prevents stale connections)
    pool_recycle=300,         # Recycle connections after 300 seconds (prevents timeout)
    pool_timeout=10,          # Timeout after 10 seconds if no connections available
    connect_args={"connect_timeout": 10},  # Timeout after 10 seconds if can't connect
)

# Session factory — creates new sessions for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for all models — provides common SQLAlchemy functionality
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session per request.
    
    This function is injected into endpoints via Depends(get_db).
    It creates a new session, yields it, and closes it when done.
    
    Usage in endpoints:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        SQLAlchemy Session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Always close the session, even if an error occurs


def check_db_connection() -> dict:
    """
    Health check endpoint that verifies database connectivity.
    
    Returns:
        {"status": "ok"} if connected
        {"status": "error", "detail": "..."} if connection fails
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # Simple query to test connection
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
