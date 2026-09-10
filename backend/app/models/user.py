"""
User Model — Authentication and Profile

This module defines the data model for users:
- User: Main model for user accounts

Users are the core entity that all other data is tied to.
Each user has their own assignments, jobs, workouts, and expenses.
"""

import uuid
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """
    User account with profile and preferences.
    
    Each row represents one user with:
    - email: Unique email for login
    - hashed_password: Bcrypt-hashed password
    - name: Display name
    - monthly_budget: Monthly spending budget (default $200)
    - weekly_capacity_hours: Weekly study/work capacity (default 40h)
    
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
