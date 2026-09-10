"""
AI Usage Log Model — Tracks API Costs and Performance

This module defines the data model for tracking AI API usage:
- AIUsageLog: Stores token usage, cost estimates, and latency

This data powers the cost monitoring dashboard and helps understand
how much the AI features cost to run.
"""

import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.base import TimestampMixin


class AIUsageLog(Base, TimestampMixin):
    """
    Tracks AI API usage for cost monitoring and performance analysis.
    
    Each row represents one AI API call with:
    - user_id: The user who triggered the call
    - endpoint: Which endpoint triggered it (daily, weekly)
    - model: Which AI model was used (claude-haiku-4-5-20251001)
    - input_tokens: Number of tokens in the prompt
    - output_tokens: Number of tokens in the response
    - estimated_cost_usd: Estimated cost in USD
    - latency_ms: How long the API call took
    - tool_calls: Number of tool calls (0 for simple prompts)
    
    Cost estimation (Claude Haiku):
    - Input: $0.25 per 1M tokens
    - Output: $1.25 per 1M tokens
    
    Example cost: 500 input tokens + 200 output tokens = $0.000275
    """
    __tablename__ = "ai_usage_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    endpoint = Column(String, nullable=False)  # "daily" or "weekly"
    model = Column(String, nullable=False)  # "claude-haiku-4-5-20251001"
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    estimated_cost_usd = Column(Float, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    tool_calls = Column(Integer, default=0, nullable=False)
