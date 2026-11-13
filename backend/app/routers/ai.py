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
    "generated_at": "2026-09-10T...",
    "sample": false
}

"sample" is true only when the account has no data at all (no assignments,
jobs, workouts, or expenses) and the briefing is a generic example. Every
POST /ai/briefing and POST /ai/refresh response includes the key.
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

# Initialize Anthropic client — None if API key not set (triggers fallback mode).
# A timeout prevents a stalled provider call from holding a request open;
# one retry covers transient connection errors without multiplying latency.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
client = (
    anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY,
        timeout=20.0,
        max_retries=1,
    )
    if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-anthropic-key"
    else None
)

# Shared grounding contract for every AI-generated insight. The model writes
# prose; it does not get to invent facts. Retrieved records are verbatim rows
# from the user's own data, so specifics must come from there.
GROUNDING_RULES = """
Grounding rules:
- The context's "retrieved_records" are verbatim records from the user's own data.
- Use them for specifics (titles, companies, amounts, dates). Never invent records, numbers, or deadlines.
- If "retrieved_records" is empty, rely on the aggregate fields and stay general.
- Never mention the context format, JSON, or retrieval process to the user.
"""

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


def account_is_empty(db: Session, user_id) -> bool:
    """
    True when the user has no assignments, job applications, workouts,
    or expenses.

    This runs before any cache read or provider call so a brand-new
    account never reaches the AI client, even if a stale insight row
    existed. Soft-deleted assignments do not count as data.
    """
    has_assignment = (
        db.query(Assignment.id)
        .filter(Assignment.user_id == user_id, Assignment.deleted_at.is_(None))
        .first()
        is not None
    )
    if has_assignment:
        return False
    if db.query(JobApplication.id).filter(JobApplication.user_id == user_id).first():
        return False
    if db.query(Workout.id).filter(Workout.user_id == user_id).first():
        return False
    return db.query(Expense.id).filter(Expense.user_id == user_id).first() is None


def with_sample(briefing: dict, sample: bool) -> dict:
    """
    Tag a briefing dict with the "sample" contract key.

    Added here in the route layer (not inside parse or the fallback
    generator) so both helpers keep their existing shapes and every
    /briefing response still reports whether it came from real data.
    """
    briefing["sample"] = sample
    return briefing


def parse_briefing(content: str, generated_at, cached: bool = True, scores: list = None, retrieval: dict = None, quick_actions: list = None):
    """
    Parse AI response into structured format.
    
    Handles two cases:
    1. AI returned valid JSON → extract priorities and summary
    2. AI returned malformed JSON → fallback to raw content as summary
    
    The scores parameter adds deterministic scoring metadata to the response,
    regardless of whether the AI or fallback generated the priorities.
    The retrieval parameter reports which records grounded the generation.
    Quick actions are computed from scores, not from the model, so they remain
    available on cached briefings and when AI is unavailable.
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
            "retrieval": retrieval,
            "quick_actions": quick_actions or [],
            "cached": cached,
            "generated_at": generated_at,
        }
    except (json.JSONDecodeError, AttributeError):
        # JSON parsing failed — return raw content as summary
        return {
            "priorities": [],
            "summary": content,
            "scores": scores or [],
            "retrieval": retrieval,
            "quick_actions": quick_actions or [],
            "cached": cached,
            "generated_at": generated_at,
        }


def build_quick_actions(signals: list, limit: int = 3) -> list:
    """
    Turn the top scored assignment signals into one-click actions.

    Quick actions are deliberately derived from the same deterministic scores
    as the briefing priorities. That keeps the treatment honest: the shortcut
    completes the work the briefing already told the user to do, rather than
    introducing a separate recommendation system.

    Non-assignment signals are skipped because "complete" is only meaningful
    for a concrete assignment row. Duplicate assignment IDs are removed.
    """
    actions = []
    seen = set()
    for signal in signals:
        if signal.domain != "assignment":
            continue
        assignment_id = signal.meta.get("assignment_id")
        if not assignment_id or assignment_id in seen:
            continue
        seen.add(assignment_id)
        actions.append({
            "assignment_id": assignment_id,
            "title": signal.title,
            "course": signal.meta.get("course"),
            "score": signal.score,
            "action": "complete",
            "label": "Mark done",
        })
        if len(actions) >= limit:
            break
    return actions


def summarize_retrieval(context: dict) -> dict:
    """Compact retrieval metadata for the API response (not sent to the model)."""
    records = context.get("retrieved_records", [])
    return {
        "chunks": len(records),
        "query": context.get("retrieval_query", ""),
        "sources": sorted({record["type"] for record in records}),
    }


def generate_fallback_briefing(db: Session, user: User, signals: list = None):
    """
    Generate briefing using deterministic scoring (no AI required).
    
    This is the "thesis-defining" feature — when AI is unavailable,
    the system uses weighted scoring to rank signals by urgency.
    The scoring rubric is transparent and deterministic.

    `signals` can be passed by callers that already scored the user, avoiding
    a second round of queries and guaranteeing quick actions match the
    priorities they came from.
    """
    now = datetime.now(timezone.utc)
    
    # Get scored signals from all 4 domains
    if signals is None:
        signals = score_signals(db, user)

    quick_actions = build_quick_actions(signals)

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
        "retrieval": None,
        "quick_actions": quick_actions,
        "cached": False,
        "generated_at": now,
    }


def generate_insight(
    db: Session,
    user: User,
    insight_type: InsightType,
    prompt: str,
    signals: list = None,
) -> tuple[AIInsight, dict]:
    """
    Generate an AI insight using Claude and persist it to the database.
    
    This function:
    1. Builds context from the user's data (aggregates + RAG-retrieved records)
    2. Sends the context + prompt to Claude
    3. Logs token usage and latency
    4. Persists the insight to ai_insights table
    5. Persists usage stats to ai_usage_log table

    Provider failures are translated to ValueError so every caller can fall
    back to the deterministic briefing instead of returning a 500.

    Returns:
        (insight, context) — context is returned so the route can report
        retrieval metadata without querying the index twice.
    """
    if not client:
        raise ValueError("AI service not configured. Set a valid ANTHROPIC_API_KEY.")

    context = build_context(db, user, signals=signals)
    # JSON, not Python repr: the model gets a stable, parseable structure and
    # non-JSON types (datetimes, Decimals) are stringified explicitly.
    context_json = json.dumps(context, default=str)
    start_time = time.time()

    # Call Claude API with the prompt and context
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n{GROUNDING_RULES}\n\nContext:\n{context_json}"
                }
            ]
        )
    except anthropic.APIError as exc:
        logger.error(
            "ai_call_failed",
            user_id=str(user.id),
            insight_type=insight_type.value,
            error_type=type(exc).__name__,
            error=str(exc)[:200],
        )
        raise ValueError("AI service unavailable") from exc

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
        retrieval_chunks=len(context.get("retrieved_records", [])),
        cached=False
    )

    content = "".join(
        block.text for block in message.content
        if getattr(block, "type", "") == "text"
    )
    if not content:
        raise ValueError("AI returned an empty response")

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
    return insight, context


@router.post("/briefing")
def get_briefing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get daily briefing — AI-powered with deterministic scoring.
    
    Flow:
    0. Empty account (no assignments/jobs/workouts/expenses) → sample
       fallback, no cache read and no AI call
    1. Always compute scores (for transparency metadata)
    2. Check cache (6-hour TTL)
    3. If no cache and AI available → generate with Claude
    4. If no cache and AI unavailable → use fallback scoring
    """
    # Always compute scores for transparency metadata
    signals = score_signals(db, current_user)
    scores = [{"domain": s.domain, "score": s.score, "title": s.title} for s in signals[:5]]
    quick_actions = build_quick_actions(signals)

    # Empty accounts are checked first so they can never hit the AI client
    # or the insight cache, no matter what rows are lying around.
    if account_is_empty(db, current_user.id):
        logger.info("briefing_sample_fallback", user_id=str(current_user.id))
        return with_sample(
            generate_fallback_briefing(db, current_user, signals=signals),
            sample=True,
        )

    # Check cache first
    cached = get_cached_insight(db, current_user.id, InsightType.daily)
    if cached:
        logger.info("ai_call", user_id=str(current_user.id), cached=True)
        return with_sample(
            parse_briefing(
                cached.content,
                cached.generated_at,
                scores=scores,
                quick_actions=quick_actions,
            ),
            sample=False,
        )

    # No cache — use AI or fallback
    if not client:
        return with_sample(
            generate_fallback_briefing(db, current_user, signals=signals),
            sample=False,
        )

    try:
        insight, context = generate_insight(
            db, current_user, InsightType.daily, DAILY_PROMPT, signals=signals
        )
        return with_sample(
            parse_briefing(
                insight.content,
                insight.generated_at,
                cached=False,
                scores=scores,
                retrieval=summarize_retrieval(context),
                quick_actions=quick_actions,
            ),
            sample=False,
        )
    except ValueError:
        return with_sample(
            generate_fallback_briefing(db, current_user, signals=signals),
            sample=False,
        )


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
        # Weekly digests benefit from the same grounding: current signals are
        # the best available proxy for what the week's evidence should cover.
        signals = score_signals(db, current_user)
        insight, _ = generate_insight(
            db, current_user, InsightType.weekly, WEEKLY_PROMPT, signals=signals
        )
        return {"content": insight.content, "cached": False, "generated_at": insight.generated_at}
    except ValueError:
        return {"content": "AI service unavailable", "cached": False, "generated_at": None}


@router.post("/refresh")
def refresh_briefing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Force refresh briefing — bypasses cache. Cache prevents redundant AI calls anyway."""
    signals = score_signals(db, current_user)
    scores = [{"domain": s.domain, "score": s.score, "title": s.title} for s in signals[:5]]
    quick_actions = build_quick_actions(signals)

    # Same empty-account guard as /briefing: no provider call, no cache write.
    if account_is_empty(db, current_user.id):
        logger.info("briefing_sample_fallback", user_id=str(current_user.id))
        return with_sample(
            generate_fallback_briefing(db, current_user, signals=signals),
            sample=True,
        )

    if not client:
        return with_sample(
            generate_fallback_briefing(db, current_user, signals=signals),
            sample=False,
        )

    try:
        insight, context = generate_insight(
            db, current_user, InsightType.daily, DAILY_PROMPT, signals=signals
        )
        return with_sample(
            parse_briefing(
                insight.content,
                insight.generated_at,
                cached=False,
                scores=scores,
                retrieval=summarize_retrieval(context),
                quick_actions=quick_actions,
            ),
            sample=False,
        )
    except ValueError:
        return with_sample(
            generate_fallback_briefing(db, current_user, signals=signals),
            sample=False,
        )

