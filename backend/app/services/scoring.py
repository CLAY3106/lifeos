"""
Scoring Service — Deterministic AI Briefing Scoring

This module implements a weighted scoring system for the AI briefing.
Instead of relying on positional priority (overdue first, then upcoming, etc.),
each signal gets a numeric score (0-100) based on urgency and impact.

The scoring rubric:
- Overdue assignments: 50 + min(days_overdue * 5, 50) — grows with age, caps at 100
- Assignment due within 24h: 90 — near-certain failure if missed
- Assignment due within 3 days: 70 — high urgency
- Assignment due within 7 days: 40 — moderate
- Job follow-up overdue: 60 — career impact
- Days since workout ≥ 5: 50 — habit decay curve
- Days since workout ≥ 3: 30 — gentle nudge
- Budget > 80% spent: 55 — financial risk
- Budget > 95% spent: 85 — critical
- Cross-domain tensions: +20 bonus — assignments due same day as interviews

This is what you tell interviewers: "deterministic scoring with model-only phrasing."
"""

from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense
from app.services.expenses_service import get_period_bounds, CATEGORY_TO_GROUP
from datetime import datetime, timezone, timedelta


@dataclass
class ScoredSignal:
    """
    A single scored signal from any domain.
    
    Attributes:
        domain: Which life area this signal comes from
               ("assignment", "job", "fitness", "finance", "tension")
        title: Short action phrase (e.g., "Overdue: DSA Assignment")
        reason: One sentence explaining why this is urgent
        score: Numeric urgency score (0-100, higher = more urgent)
        meta: Additional context (assignment_id, days_left, course, etc.)
    """
    domain: str
    title: str
    reason: str
    score: float
    meta: dict


def score_signals(db: Session, user: User) -> list[ScoredSignal]:
    """
    Query all 4 domains and return scored signals sorted by score descending.
    
    This is the core function that powers the AI briefing. It:
    1. Queries assignments, jobs, workouts, and expenses
    2. Applies the scoring rubric to each signal
    3. Detects cross-domain tensions (e.g., deadline collisions)
    4. Returns signals sorted by urgency (highest score first)
    
    The frontend uses these scores to:
    - Display priorities ranked by urgency
    - Show score metadata for transparency
    - Highlight cross-domain tensions
    """
    now = datetime.now(timezone.utc)
    week_from_now = now + timedelta(days=7)
    signals = []

    # ==============================
    # ASSIGNMENTS — Academic deadlines
    # ==============================
    
    # Query overdue assignments (due date < now, status = pending, not deleted)
    overdue = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date < now
    ).order_by(Assignment.due_date).all()

    # Score each overdue assignment: grows with age, caps at 100
    for a in overdue:
        days_overdue = (now - a.due_date.replace(tzinfo=timezone.utc)).days
        score = min(50 + days_overdue * 5, 100)  # 50 base + 5 per day, max 100
        signals.append(ScoredSignal(
            domain="assignment",
            title=f"Overdue: {a.title}",
            reason=f"This was due {days_overdue} day{'s' if days_overdue != 1 else ''} ago.",
            score=score,
            meta={"assignment_id": str(a.id), "days_overdue": days_overdue, "course": a.course}
        ))

    # Query upcoming assignments (due within 7 days)
    upcoming = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date >= now,
        Assignment.due_date <= week_from_now
    ).order_by(Assignment.due_date).all()

    # Score based on proximity to deadline
    for a in upcoming:
        days_left = (a.due_date.replace(tzinfo=timezone.utc) - now).days
        if days_left <= 1:
            score = 90   # Due tomorrow or today — almost certain failure
        elif days_left <= 3:
            score = 70   # Due in 2-3 days — high urgency
        else:
            score = 40   # Due in 4-7 days — moderate
        signals.append(ScoredSignal(
            domain="assignment",
            title=f"Due soon: {a.title}",
            reason=f"Deadline in {days_left} day{'s' if days_left != 1 else ''} — estimated {a.estimated_hours}h of work.",
            score=score,
            meta={"assignment_id": str(a.id), "days_left": days_left, "course": a.course}
        ))

    # ==============================
    # JOBS — Career follow-ups
    # ==============================
    
    # Query jobs where follow-up date has passed (status = applied, not yet followed up)
    overdue_followups = db.query(JobApplication).filter(
        JobApplication.user_id == user.id,
        JobApplication.followup_date < now,
        JobApplication.status == JobStatus.applied
    ).all()

    # Fixed score of 60 — career impact but not as urgent as overdue assignments
    for job in overdue_followups:
        days_since = (now - job.followup_date.replace(tzinfo=timezone.utc)).days
        signals.append(ScoredSignal(
            domain="job",
            title=f"Follow up: {job.role} at {job.company}",
            reason=f"Applied {days_since} day{'s' if days_since != 1 else ''} ago with no response.",
            score=60,
            meta={"job_id": str(job.id), "days_since_applied": days_since}
        ))

    # ==============================
    # FITNESS — Workout consistency
    # ==============================
    
    # Query most recent workout
    last_workout = db.query(Workout).filter(
        Workout.user_id == user.id
    ).order_by(Workout.logged_at.desc()).first()

    if last_workout and last_workout.logged_at:
        days_since = (now - last_workout.logged_at.replace(tzinfo=timezone.utc)).days
        # Score based on habit decay curve
        if days_since >= 5:
            score = 50   # Very overdue — habit is breaking
        elif days_since >= 3:
            score = 30   # Gentle nudge — still salvageable
        else:
            score = 0    # Recently worked out — no signal needed
        if score > 0:
            signals.append(ScoredSignal(
                domain="fitness",
                title="Get a workout in",
                reason=f"It's been {days_since} days since your last session.",
                score=score,
                meta={"days_since_workout": days_since}
            ))
    else:
        # Never worked out — moderate urgency to start
        signals.append(ScoredSignal(
            domain="fitness",
            title="Start a workout routine",
            reason="You haven't logged any workouts yet.",
            score=40,
            meta={"days_since_workout": None}
        ))

    # ==============================
    # FINANCE — Budget utilization
    # ==============================
    
    # Get current month's expenses using the period bounds helper
    start, end = get_period_bounds("month")
    monthly_expenses = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.spent_at >= start,
        Expense.spent_at < end
    ).all()
    total_spent = sum(e.amount for e in monthly_expenses)

    # Only score if user has a budget set
    if user.monthly_budget and user.monthly_budget > 0:
        percent = (total_spent / user.monthly_budget) * 100
        # Score based on budget utilization thresholds
        if percent >= 95:
            score = 85   # Critical — almost out of budget
        elif percent >= 80:
            score = 55   # Warning — approaching limit
        else:
            score = 0    # Under 80% — no signal needed
        if score > 0:
            remaining = user.monthly_budget - total_spent
            signals.append(ScoredSignal(
                domain="finance",
                title="Watch your spending",
                reason=f"You've used {round(percent)}% of your ${user.monthly_budget:.0f} budget — ${remaining:.2f} left.",
                score=score,
                meta={"percent": round(percent, 1), "remaining": round(remaining, 2)}
            ))

    # ==============================
    # CROSS-DOMAIN TENSIONS
    # ==============================
    
    # Detect assignments due same day as job applications/interviews
    assignment_deadlines = [a.due_date.date() for a in upcoming]
    job_dates = [j.applied_date for j in db.query(JobApplication).filter(
        JobApplication.user_id == user.id,
        JobApplication.status.in_([JobStatus.applied, JobStatus.oa])
    ).all()]

    # Check for date collisions between assignments and jobs
    for a_date in assignment_deadlines:
        for j_date in job_dates:
            if a_date == j_date:
                signals.append(ScoredSignal(
                    domain="tension",
                    title="Deadline collision detected",
                    reason=f"Assignment due same day as job activity on {a_date}.",
                    score=70,
                    meta={"date": str(a_date)}
                ))

    # Detect weekly overload (> 80% of capacity)
    if user.weekly_capacity_hours and user.weekly_capacity_hours > 0:
        weekly_load = sum(a.estimated_hours for a in upcoming)
        load_percent = (weekly_load / user.weekly_capacity_hours) * 100
        if load_percent > 80:
            signals.append(ScoredSignal(
                domain="tension",
                title="Weekly overload",
                reason=f"You're at {round(load_percent)}% capacity this week.",
                score=65,
                meta={"load_percent": round(load_percent, 1)}
            ))

    # Return all signals sorted by urgency (highest score first)
    return sorted(signals, key=lambda s: s.score, reverse=True)
