"""
Base Model — Timestamp Mixin for All Models

This module provides a reusable mixin for adding timestamps to models:
- TimestampMixin: Adds created_at and updated_at columns

All models that need timestamps should inherit from this mixin.
The timestamps are automatically set on creation and update.
"""

from sqlalchemy import Column, DateTime
from datetime import datetime, timezone


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps to a model.
    
    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_model"
            id = Column(UUID, primary_key=True)
            # created_at and updated_at are automatically added
    
    Behavior:
    - created_at: Set to current UTC time when the row is created
    - updated_at: Set to current UTC time when the row is created
    - updated_at: Automatically updated to current UTC time on any update
    
    The timestamps use timezone-aware UTC datetimes to avoid
    timezone confusion across different servers and clients.
    """
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
