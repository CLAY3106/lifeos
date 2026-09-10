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
from app.services.context_builder import build_context
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

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-anthropic-key" else None

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

WEEKLY_PROMPT = """You are a personal life coach for a college student.
Given the context below, write a brief Sunday digest (3-4 sentences) covering:
1. Academic progress this week
2. Job search momentum
3. Fitness consistency
4. Spending vs budget

Be honest and encouraging. No filler."""

def get_cached_insight(db: Session, user_id, insight_type: InsightType):
    six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6)
    return db.query(AIInsight).filter(
        AIInsight.user_id == user_id,
        AIInsight.type == insight_type,
        AIInsight.generated_at >= six_hours_ago
    ).first()

import re

def parse_briefing(content: str, generated_at, cached: bool = True):
    cleaned = content.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()
    try:
        data = json.loads(cleaned)
        return {
            "priorities": data.get("priorities", []),
            "summary": data.get("summary", ""),
            "cached": cached,
            "generated_at": generated_at,
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "priorities": [],
            "summary": content,
            "cached": cached,
            "generated_at": generated_at,
        }

def generate_fallback_briefing(db: Session, user: User):
    now = datetime.now(timezone.utc)
    week_from_now = now + timedelta(days=7)
    priorities = []

    # 1. Overdue assignments (highest priority)
    overdue = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date < now
    ).order_by(Assignment.due_date).all()
    if overdue:
        a = overdue[0]
        days_overdue = (now - a.due_date.replace(tzinfo=timezone.utc)).days
        priorities.append({
            "title": f"Overdue: {a.title}",
            "reason": f"This was due {days_overdue} day{'s' if days_overdue != 1 else ''} ago — submit it as soon as possible."
        })

    # 2. Nearest upcoming deadline
    upcoming = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date >= now,
        Assignment.due_date <= week_from_now
    ).order_by(Assignment.due_date).limit(2).all()
    for a in upcoming:
        if len(priorities) >= 3:
            break
        days_left = (a.due_date.replace(tzinfo=timezone.utc) - now).days
        priorities.append({
            "title": f"Due soon: {a.title}",
            "reason": f"Deadline in {days_left} day{'s' if days_left != 1 else ''} — estimated {a.estimated_hours}h of work."
        })

    # 3. Job follow-ups or fitness gap or budget
    if len(priorities) < 3:
        overdue_followups = db.query(JobApplication).filter(
            JobApplication.user_id == user.id,
            JobApplication.followup_date < now,
            JobApplication.status == JobStatus.applied
        ).count()
        if overdue_followups > 0:
            priorities.append({
                "title": f"Follow up on {overdue_followups} job application{'s' if overdue_followups != 1 else ''}",
                "reason": "You applied over a week ago with no response — send a polite follow-up."
            })

    if len(priorities) < 3:
        last_workout = db.query(Workout).filter(
            Workout.user_id == user.id
        ).order_by(Workout.logged_at.desc()).first()
        if last_workout and last_workout.logged_at:
            days_since = (now - last_workout.logged_at.replace(tzinfo=timezone.utc)).days
            if days_since >= 3:
                priorities.append({
                    "title": "Get a workout in",
                    "reason": f"It's been {days_since} days since your last session — even 20 minutes counts."
                })

    if len(priorities) < 3:
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0)
        monthly_spent = db.query(Expense).filter(
            Expense.user_id == user.id,
            Expense.spent_at >= start_of_month
        ).all()
        total = sum(e.amount for e in monthly_spent)
        if user.monthly_budget and total > user.monthly_budget * 0.8:
            remaining = user.monthly_budget - total
            priorities.append({
                "title": "Watch your spending",
                "reason": f"You've used {round(total / user.monthly_budget * 100)}% of your ${user.monthly_budget:.0f} budget — ${remaining:.2f} left this month."
            })

    # Ensure exactly 3 priorities
    while len(priorities) < 3:
        priorities.append({
            "title": "Stay on track",
            "reason": "You're doing well — keep building momentum across all your goals."
        })

    summary_parts = []
    if overdue:
        summary_parts.append(f"{len(overdue)} overdue assignment{'s' if len(overdue) != 1 else ''}")
    if upcoming:
        summary_parts.append(f"{len(upcoming)} due this week")
    summary = "Today's focus: " + ", ".join(summary_parts) + "." if summary_parts else "No urgent deadlines today — use this time to get ahead."

    return {
        "priorities": priorities[:3],
        "summary": summary,
        "cached": False,
        "generated_at": now,
    }

# generate insight of the user which is stored in the database, then store the insight into the database
def generate_insight(db: Session, user: User, insight_type: InsightType, prompt: str) -> AIInsight:
    if not client:
        raise ValueError("AI service not configured. Set a valid ANTHROPIC_API_KEY.")

    context = build_context(db, user)
    start_time = time.time()

    # create messages for models with prompts to generate insight
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

    # calculate latency
    latency_ms = round((time.time() - start_time) * 1000)
    # get input tokens
    input_tokens = message.usage.input_tokens
    # get output tokens
    output_tokens = message.usage.output_tokens
    # estimate and round the cost for one insight generation
    estimated_cost = round((input_tokens * 0.00000025) + (output_tokens * 0.00000125), 6)

    # log each insight generation
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

    content = message.content[0].text

    # create insight information including id, user id, type, content, and generation time
    insight = AIInsight(
        id=uuid.uuid4(),
        user_id=user.id,
        type=insight_type,
        content=content,
        generated_at=datetime.now(timezone.utc)
    )
    # add the insight into the database
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
    cached = get_cached_insight(db, current_user.id, InsightType.daily)
    if cached:
        logger.info("ai_call", user_id=str(current_user.id), cached=True)
        return parse_briefing(cached.content, cached.generated_at)

    if not client:
        return generate_fallback_briefing(db, current_user)

    try:
        insight = generate_insight(db, current_user, InsightType.daily, DAILY_PROMPT)
        return parse_briefing(insight.content, insight.generated_at, cached=False)
    except ValueError as e:
        return generate_fallback_briefing(db, current_user)
@router.post("/weekly")
@limiter.limit("5/day")
def get_weekly(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
@limiter.limit("10/day")
def refresh_briefing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not client:
        return generate_fallback_briefing(db, current_user)

    try:
        insight = generate_insight(db, current_user, InsightType.daily, DAILY_PROMPT)
        return parse_briefing(insight.content, insight.generated_at, cached=False)
    except ValueError as e:
        return generate_fallback_briefing(db, current_user)
