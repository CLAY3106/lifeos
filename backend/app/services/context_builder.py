"""
Context Builder — Gathers User Data for the AI Briefing

The briefing context has two layers:

1. Aggregates (structured): counts, percentages, and totals across the four
   domains. Cheap, deterministic, and always available.
2. Retrieved records (RAG): the specific rows most relevant to today's top
   scored signals. These give the model concrete titles, companies, amounts,
   and dates instead of asking it to guess from totals.

Why derive the retrieval query from the scoring signals?
--------------------------------------------------------
A daily briefing has no user query. The deterministic scoring service already
answers "what matters today", so its top signals become the retrieval query:
the scorer decides *what* to talk about, retrieval fetches the *evidence*, and
the LLM only writes the phrasing. This keeps the model grounded and makes the
whole pipeline debuggable — every priority traces back to a score and a chunk.

Retrieval is fail-open: if the index is empty or the search raises, the
briefing is still generated from the aggregate layer.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.logger import logger
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense
from app.services.rag import hybrid_search
from app.services.scoring import ScoredSignal

# How many chunks to retrieve. Eight is enough to cover the top three signals
# with a few related records each, without bloating the prompt.
RETRIEVAL_LIMIT = 8

# Used when there are no scored signals (e.g. a quiet week, or the weekly
# digest which does not compute scores). Keeps retrieval domain-agnostic.
DEFAULT_RETRIEVAL_QUERY = (
    "overdue assignments, upcoming deadlines, job application follow-ups, "
    "recent spending, workout consistency"
)


def build_retrieval_query(signals: Optional[list[ScoredSignal]]) -> str:
    """
    Turn the top scored signals into a natural-language retrieval query.

    Titles carry the concrete nouns ("DSA Assignment", "SWE Intern at Google")
    while the domain tag helps keyword search. Reasons are excluded because
    they contain relative dates ("3 days ago") that add noise without matching
    any stored chunk.
    """
    if not signals:
        return DEFAULT_RETRIEVAL_QUERY

    return " ".join(f"{s.title} ({s.domain})" for s in signals[:3])


def retrieve_records(
    db: Session,
    user: User,
    signals: Optional[list[ScoredSignal]] = None,
    limit: int = RETRIEVAL_LIMIT,
) -> list[dict]:
    """
    Retrieve the chunks most relevant to today's signals.

    Returns a list of {"type", "content"} dicts ready for JSON serialization.
    Any failure returns [] so a retrieval outage degrades the briefing's
    specificity, never its availability.
    """
    query = build_retrieval_query(signals)

    try:
        chunks = hybrid_search(db, user.id, query, limit=limit)
    except Exception as exc:  # noqa: BLE001 — retrieval must fail open
        logger.warning(
            "rag_retrieval_failed",
            user_id=str(user.id),
            error_type=type(exc).__name__,
            error=str(exc)[:200],
        )
        return []

    logger.info(
        "rag_retrieval",
        user_id=str(user.id),
        query=query,
        chunks=len(chunks),
        # A vector score on any chunk means the semantic path contributed.
        # No chunks at all is a third state: the index is empty or nothing
        # matched, which is different from a keyword-only fallback.
        mode=(
            "none" if not chunks
            else "hybrid" if any(c.get("vector_score") is not None for c in chunks)
            else "keyword"
        ),
    )

    return [
        {"type": chunk["entity_type"], "content": chunk["content"]}
        for chunk in chunks
    ]


def build_context(
    db: Session,
    user: User,
    signals: Optional[list[ScoredSignal]] = None,
) -> dict:
    """
    Build the full briefing context from the user's data.

    Args:
        db: Database session.
        user: Authenticated user.
        signals: Scored signals from scoring.score_signals(). When provided,
            they drive RAG retrieval. When omitted, a generic query is used.

    Returns:
        Dictionary with aggregate stats plus retrieved records.
    """
    now = datetime.now(timezone.utc)
    week_from_now = now + timedelta(days=7)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0)

    # ==============================
    # ASSIGNMENTS — Academic deadlines
    # ==============================

    # Query upcoming assignments (due within 7 days)
    upcoming = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date <= week_from_now
    ).order_by(Assignment.due_date).all()

    # Calculate weekly load as percentage of capacity
    weekly_load_hours = sum(a.estimated_hours for a in upcoming)
    load_percent = round((weekly_load_hours / user.weekly_capacity_hours) * 100, 1) if user.weekly_capacity_hours else 0

    # Count overdue assignments (due date < now)
    overdue = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date < now
    ).count()

    # ==============================
    # JOBS — Career tracking
    # ==============================

    # Count overdue follow-ups (follow-up date passed, status still "applied")
    overdue_followups = db.query(JobApplication).filter(
        JobApplication.user_id == user.id,
        JobApplication.followup_date < now,
        JobApplication.status == JobStatus.applied
    ).count()

    # Count total applications
    total_applications = db.query(JobApplication).filter(
        JobApplication.user_id == user.id
    ).count()

    # ==============================
    # FITNESS — Workout consistency
    # ==============================

    # Get most recent workout
    last_workout = db.query(Workout).filter(
        Workout.user_id == user.id
    ).order_by(Workout.logged_at.desc()).first()

    # Calculate days since last workout
    days_since_workout = None
    if last_workout and last_workout.logged_at:
        days_since_workout = (now - last_workout.logged_at.replace(tzinfo=timezone.utc)).days

    # ==============================
    # FINANCE — Budget utilization
    # ==============================

    # Get current month's expenses
    monthly_expenses = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.spent_at >= start_of_month
    ).all()

    # Calculate total spent and budget percentage
    total_spent = sum(e.amount for e in monthly_expenses)
    budget_percent = round((total_spent / user.monthly_budget) * 100, 1) if user.monthly_budget else 0

    # Whole days remaining in the month. Kept as an int because the context is
    # serialized to JSON — a timedelta is not JSON-serializable.
    days_left_in_month = (
        (start_of_month + timedelta(days=32)).replace(day=1) - now
    ).days

    return {
        "user_name": user.name,
        "assignments": {
            "upcoming_count": len(upcoming),
            "upcoming_titles": [a.title for a in upcoming[:3]],  # Top 3 titles for brevity
            "weekly_load_hours": weekly_load_hours,
            "weekly_capacity_hours": user.weekly_capacity_hours,
            "load_percent": load_percent,
            "overdue_count": overdue
        },
        "jobs": {
            "total_applications": total_applications,
            "overdue_followups": overdue_followups
        },
        "fitness": {
            "days_since_workout": days_since_workout
        },
        "finance": {
            "total_spent": total_spent,
            "monthly_budget": user.monthly_budget,
            "budget_percent": budget_percent,
            "days_left_in_month": days_left_in_month
        },
        "retrieval_query": build_retrieval_query(signals),
        "retrieved_records": retrieve_records(db, user, signals),
    }
