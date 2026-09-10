"""
AI Router — Briefing Generation and Caching

This module handles the AI-powered daily briefing system. It has two modes:
1. AI-powered: Uses Claude to generate personalized briefings (when API key is set)
2. Fallback: Uses deterministic scoring to generate briefings (when AI is unavailable)

The scoring system (from scoring.py) powers both modes:
- AI mode: Scores are returned alongside AI response for transparency
- Fallback mode: Scores determine the top 3 priorities

Response shape:
{
    "priorities": [{"title": "...", "reason": "...", "score": 92, "domain": "assignment"}],
    "summary": "Today's focus: assignment: overdue dsa assignment, fitness: get a workout in.",
    "scores": [{"domain": "assignment", "score": 92, "title": "..."}],
    "cached": false,
    "generated_at": "2026-09-10T..."
}
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.ai_insight import AIInsight, InsightType
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense
from app.models.ai_usage_log import AIUsageLog
from app.services.context_builder import build_context
from app.services.scoring import score_signals
from app.logger import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timezone, timedelta
import anthropic
import uuid
import os
import time
import json
import re

router = APIRouter(prefix="/ai", tags=["ai"])
limiter = Limiter(key_func=get_remote_address)

# Initialize Anthropic client — None if API key not set (triggers fallback mode)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-anthropic-key" else None

# Prompt for daily briefing — asks for JSON with priorities and summary
DAILY_PROMPT = """You are a personal life coach for a college student.
Given the context below, return a JSON object with exactly two fields:

1. "priorities" — an array of exactly 3 objects, each with:
   - "title": a short action phrase (e.g. "Submit DSA assignment")
   - "reason": one sentence explaining why this is urgent

2. "summary" — a 1-2 sentence overall briefing covering the day

Rules:
- Rank priorities by urgency (deadline soonest, or biggest risk)
- Each priority must be specific and actionable
- Never return more than 3 priorities
- Return ONLY valid JSON, no markdown, no explanation

Example format:
{"priorities": [{"title": "...", "reason": "..."}, {"title": "...", "reason": "..."}, {"title": "...", "reason": "..."}], "summary": "..."}"""

# Prompt for weekly digest — asks for plain text summary
WEEKLY_PROMPT = """You are a personal life coach for a college student.
Given the context below, write a brief Sunday digest (3-4 sentences) covering:
1. Academic progress this week
2. Job search momentum
3. Fitness consistency
4. Spending vs budget

Be honest and encouraging. No filler."""


def get_cached_insight(db: Session, user_id, insight_type: InsightType):
    """Check if we have a recent insight (within 6 hours) to avoid redundant AI calls."""
    six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6)
    return db.query(AIInsight).filter(
        AIInsight.user_id == user_id,
        AIInsight.type == insight_type,
        AIInsight.generated_at >= six_hours_ago
    ).first()


def parse_briefing(content: str, generated_at, cached: bool = True, scores: list = None):
    """
    Parse AI response into structured format.
    
    Handles two cases:
    1. AI returned valid JSON → extract priorities and summary
    2. AI returned malformed JSON → fallback to raw content as summary
    
    The scores parameter adds deterministic scoring metadata to the response,
    regardless of whether the AI or fallback generated the priorities.
    """
    # Strip markdown code fences if present (AI sometimes wraps JSON in ```json ... ```)
    cleaned = content.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()
    
    try:
        data = json.loads(cleaned)
        return {
            "priorities": data.get("priorities", []),
            "summary": data.get("summary", ""),
            "scores": scores or [],
            "cached": cached,
            "generated_at": generated_at,
        }
    except (json.JSONDecodeError, AttributeError):
        # JSON parsing failed — return raw content as summary
        return {
            "priorities": [],
            "summary": content,
            "scores": scores or [],
            "cached": cached,
            "generated_at": generated_at,
        }


def generate_fallback_briefing(db: Session, user: User):
    """
    Generate briefing using deterministic scoring (no AI required).
    
    This is the "thesis-defining" feature — when AI is unavailable,
    the system uses weighted scoring to rank signals by urgency.
    The scoring rubric is transparent and deterministic.
    """
    now = datetime.now(timezone.utc)
    
    # Get scored signals from all 4 domains
    signals = score_signals(db, user)

    # Take top 3 signals as priorities
    priorities = []
    for s in signals[:3]:
        priorities.append({
            "title": s.title,
            "reason": s.reason,
            "score": s.score,
            "domain": s.domain
        })

    # Pad to exactly 3 if fewer signals exist
    while len(priorities) < 3:
        priorities.append({
            "title": "Stay on track",
            "reason": "You're doing well — keep building momentum across all your goals.",
            "score": 0,
            "domain": "general"
        })

    # Build summary from signal titles (one per domain, max 5)
    summary_parts = []
    domains_seen = set()
    for s in signals[:5]:
        if s.domain not in domains_seen:
            domains_seen.add(s.domain)
            summary_parts.append(f"{s.domain}: {s.title.lower()}")

    summary = "Today's focus: " + ", ".join(summary_parts) + "." if summary_parts else "No urgent deadlines today — use this time to get ahead."

    return {
        "priorities": priorities,
        "summary": summary,
        "scores": [{"domain": s.domain, "score": s.score, "title": s.title} for s in signals[:5]],
        "cached": False,
        "generated_at": now,
    }


def generate_insight(db: Session, user: User, insight_type: InsightType, prompt: str) -> AIInsight:
    """
    Generate an AI insight using Claude and persist it to the database.
    
    This function:
    1. Builds context from the user's data (assignments, jobs, workouts, expenses)
    2. Sends the context + prompt to Claude
    3. Logs token usage and latency
    4. Persists the insight to ai_insights table
    5. Persists usage stats to ai_usage_log table
    """
    if not client:
        raise ValueError("AI service not configured. Set a valid ANTHROPIC_API_KEY.")

    context = build_context(db, user)
    start_time = time.time()

    # Call Claude API with the prompt and context
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nContext:\n{context}"
            }
        ]
    )

    # Calculate latency and token usage for monitoring
    latency_ms = round((time.time() - start_time) * 1000)
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    # Estimate cost: $0.25/1M input, $1.25/1M output (Claude Haiku pricing)
    estimated_cost = round((input_tokens * 0.00000025) + (output_tokens * 0.00000125), 6)

    # Log to structured logging (for Render logs)
    logger.info(
        "ai_call",
        user_id=str(user.id),
        insight_type=insight_type.value,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=estimated_cost,
        latency_ms=latency_ms,
        cached=False
    )

    # Persist usage to ai_usage_log table (for cost tracking dashboard)
    usage_log = AIUsageLog(
        id=uuid.uuid4(),
        user_id=user.id,
        endpoint=insight_type.value,
        model="claude-haiku-4-5-20251001",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=estimated_cost,
        latency_ms=latency_ms,
        tool_calls=0
    )
    db.add(usage_log)

    content = message.content[0].text

    # Persist the insight content for caching (6-hour TTL)
    insight = AIInsight(
        id=uuid.uuid4(),
        user_id=user.id,
        type=insight_type,
        content=content,
        generated_at=datetime.now(timezone.utc)
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.post("/briefing")
def get_briefing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get daily briefing — AI-powered with deterministic scoring.
    
    Flow:
    1. Always compute scores (for transparency metadata)
    2. Check cache (6-hour TTL)
    3. If no cache and AI available → generate with Claude
    4. If no cache and AI unavailable → use fallback scoring
    """
    # Always compute scores for transparency metadata
    signals = score_signals(db, current_user)
    scores = [{"domain": s.domain, "score": s.score, "title": s.title} for s in signals[:5]]

    # Check cache first
    cached = get_cached_insight(db, current_user.id, InsightType.daily)
    if cached:
        logger.info("ai_call", user_id=str(current_user.id), cached=True)
        return parse_briefing(cached.content, cached.generated_at, scores=scores)

    # No cache — use AI or fallback
    if not client:
        return generate_fallback_briefing(db, current_user)

    try:
        insight = generate_insight(db, current_user, InsightType.daily, DAILY_PROMPT)
        return parse_briefing(insight.content, insight.generated_at, cached=False, scores=scores)
    except ValueError as e:
        return generate_fallback_briefing(db, current_user)


@router.post("/weekly")
@limiter.limit("5/day")
def get_weekly(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weekly digest — rate limited to 5 per day."""
    cached = get_cached_insight(db, current_user.id, InsightType.weekly)
    if cached:
        logger.info("ai_call", user_id=str(current_user.id), cached=True)
        return {"content": cached.content, "cached": True, "generated_at": cached.generated_at}

    try:
        insight = generate_insight(db, current_user, InsightType.weekly, WEEKLY_PROMPT)
        return {"content": insight.content, "cached": False, "generated_at": insight.generated_at}
    except ValueError as e:
        return {"content": str(e), "cached": False, "generated_at": None}


@router.post("/refresh")
def refresh_briefing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Force refresh briefing — bypasses cache. Cache prevents redundant AI calls anyway."""
    signals = score_signals(db, current_user)
    scores = [{"domain": s.domain, "score": s.score, "title": s.title} for s in signals[:5]]

    if not client:
        return generate_fallback_briefing(db, current_user)

    try:
        insight = generate_insight(db, current_user, InsightType.daily, DAILY_PROMPT)
        return parse_briefing(insight.content, insight.generated_at, cached=False, scores=scores)
    except ValueError as e:
        return generate_fallback_briefing(db, current_user)
