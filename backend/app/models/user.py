"""
User Model: Authentication and Profile

This module defines the data model for users:
- User: Main model for user accounts

Users are the core entity that all other data is tied to.
Each user has their own assignments, jobs, workouts, and expenses.
"""

import uuid
from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin

# Modules shown in onboarding and used to gate the dashboard widgets.
# Keep in sync with the server_default in alembic revision c3e5a7b9d1f4.
DEFAULT_ACTIVE_MODULES = ["academics", "jobs", "fitness", "finance"]


def default_active_modules() -> list:
    """Return a fresh copy so rows never share one mutable list."""
    return list(DEFAULT_ACTIVE_MODULES)


class User(Base, TimestampMixin):
    """
    User account with profile and preferences.
    
    Each row represents one user with:
    - email: Unique email for login
    - hashed_password: Bcrypt-hashed password
    - name: Display name
    - monthly_budget: Monthly spending budget (default $200)
    - weekly_capacity_hours: Weekly study/work capacity (default 40h)
    - onboarding_completed_at: Set once the user finishes the onboarding flow
    - active_modules: Module keys the user enabled (default: all four)
    
    The monthly_budget and weekly_capacity_hours fields are used for:
    - Budget utilization calculations in the finance domain
    - Weekly load calculations in the academic domain
    - AI briefing scoring and context building
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    monthly_budget = Column(Float, default=200)  # Default $200/month
    weekly_capacity_hours = Column(Float, default=40)  # Default 40 hours/week
    onboarding_completed_at = Column(DateTime, nullable=True)
    active_modules = Column(
        JSON,
        nullable=False,
        default=default_active_modules,
        server_default='["academics", "jobs", "fitness", "finance"]',
    )
