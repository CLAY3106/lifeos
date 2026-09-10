"""
Context Builder — Gathers User Data for AI Briefing

This module builds a context dictionary from the user's data across all 4 domains:
1. Assignments — upcoming deadlines, weekly load, overdue count
2. Jobs — total applications, overdue follow-ups
3. Fitness — days since last workout
4. Finance — total spent, budget percent, days left in month

The context is passed to the AI (Claude) as part of the prompt,
giving the model a complete picture of the user's life to generate
personalized, actionable advice.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense
from datetime import datetime, timezone, timedelta


def build_context(db: Session, user: User) -> dict:
    """
    Build a context dictionary from the user's data across all 4 domains.
    
    This function queries the database to gather:
    - Upcoming assignments and weekly load
    - Job application stats
    - Fitness consistency
    - Budget utilization
    
    The returned dict is serialized to JSON and passed to Claude as context
    in the AI briefing prompt.
    
    Args:
        db: Database session
        user: Authenticated user
    
    Returns:
        Dictionary with structured context for AI briefing
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

    # Calculate days left in month
    days_left_in_month = (start_of_month + timedelta(days=32)).replace(day=1) - now

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
        }
    }
