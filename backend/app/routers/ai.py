from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.ai_insight import AIInsight, InsightType
from app.services.context_builder import build_context
from datetime import datetime, timezone, timedelta
import anthropic
import uuid
import os

router = APIRouter(prefix="/ai", tags=["ai"])

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

DAILY_PROMPT = """You are a personal life coach for a college student. 
Given the context below, give a 2-3 sentence morning briefing that:
1. Flags the single most urgent thing today
2. Notices cross-domain tensions (e.g. heavy week + no workouts + overspending)
3. Gives one specific actionable suggestion

Be direct. No filler. No bullet points. Just 2-3 sentences."""

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

def generate_insight(db: Session, user: User, insight_type: InsightType, prompt: str) -> AIInsight:
    context = build_context(db, user)

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

    content = message.content[0].text

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cached = get_cached_insight(db, current_user.id, InsightType.daily)
    if cached:
        return {"content": cached.content, "cached": True, "generated_at": cached.generated_at}

    insight = generate_insight(db, current_user, InsightType.daily, DAILY_PROMPT)
    return {"content": insight.content, "cached": False, "generated_at": insight.generated_at}

@router.post("/weekly")
def get_weekly(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cached = get_cached_insight(db, current_user.id, InsightType.weekly)
    if cached:
        return {"content": cached.content, "cached": True, "generated_at": cached.generated_at}

    insight = generate_insight(db, current_user, InsightType.weekly, WEEKLY_PROMPT)
    return {"content": insight.content, "cached": False, "generated_at": insight.generated_at}

@router.post("/refresh")
def refresh_briefing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insight = generate_insight(db, current_user, InsightType.daily, DAILY_PROMPT)
    return {"content": insight.content, "cached": False, "generated_at": insight.generated_at}