"""
AI Insight Model — Stores Generated Briefings

This module defines the data model for AI-generated insights:
- InsightType: Enum for daily and weekly insights
- AIInsight: Stores the generated content with metadata

The insight is cached for 6 hours to avoid redundant AI calls.
The content is the raw AI response (JSON for daily, plain text for weekly).
"""

import uuid
from sqlalchemy import Column, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum


class InsightType(enum.Enum):
    """
    Types of AI insights that can be generated.
    
    - daily: Daily briefing with priorities and summary (JSON format)
    - weekly: Weekly digest with 3-4 sentence summary (plain text)
    """
    daily = "daily"
    weekly = "weekly"


class AIInsight(Base, TimestampMixin):
    """
    Stores AI-generated insights for caching and retrieval.
    
    Each row represents one AI-generated insight with:
    - user_id: The user this insight belongs to
    - type: Daily or weekly insight
    - content: The raw AI response (JSON or plain text)
    - generated_at: When the insight was generated (for 6-hour cache TTL)
    
    The insight is cached for 6 hours to avoid redundant AI calls.
    After 6 hours, a new insight is generated on the next request.
    """
    __tablename__ = "ai_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(InsightType), nullable=False)
    content = Column(Text, nullable=False)  # Raw AI response (JSON or plain text)
    generated_at = Column(DateTime, nullable=True)  # For 6-hour cache TTL
