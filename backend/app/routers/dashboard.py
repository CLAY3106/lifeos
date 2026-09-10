"""
Dashboard Router — Aggregated Data for Frontend Dashboard

This module provides the main dashboard endpoint that aggregates
data from all four domains (assignments, jobs, fitness, finance)
into a single response for the frontend dashboard.

The dashboard shows:
- Upcoming assignments due in the next 7 days
- Weekly load hours vs capacity
- Overdue job follow-ups
- Days since last workout
- Monthly spending vs budget
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated dashboard data for the current user.
    
    This endpoint combines data from all four domains:
    1. Assignments: Upcoming tasks due in 7 days, weekly load
    2. Jobs: Overdue follow-ups
    3. Fitness: Days since last workout
    4. Finance: Monthly spending vs budget
    
    Returns a single JSON response with all the data needed
    for the frontend dashboard.
    """
    now = datetime.now(timezone.utc)
    week_from_now = now + timedelta(days=7)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0)

    # Get upcoming assignments (pending, due within 7 days)
    upcoming_assignments = db.query(Assignment).filter(
        Assignment.user_id == current_user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date <= week_from_now
    ).order_by(Assignment.due_date).all()

    # Calculate weekly load from upcoming assignments
    weekly_load_hours = sum(a.estimated_hours for a in upcoming_assignments)

    # Count overdue job follow-ups (applied but follow-up date passed)
    overdue_followups = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.followup_date < now,
        JobApplication.status == JobStatus.applied
    ).count()

    # Get last workout and calculate days since
    last_workout = db.query(Workout).filter(
        Workout.user_id == current_user.id
    ).order_by(Workout.logged_at.desc()).first()

    days_since_workout = None
    if last_workout and last_workout.logged_at:
        days_since_workout = (now - last_workout.logged_at.replace(tzinfo=timezone.utc)).days

    # Calculate monthly spending
    monthly_expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.spent_at >= start_of_month
    ).all()

    total_spent = sum(e.amount for e in monthly_expenses)
    budget_percent = round((total_spent / current_user.monthly_budget) * 100, 1) if current_user.monthly_budget else 0

    # Return aggregated dashboard data
    return {
        "user": {"name": current_user.name, "email": current_user.email},
        "assignments": {
            "upcoming": [{"id": str(a.id), "title": a.title, "course": a.course, "due_date": a.due_date, "estimated_hours": a.estimated_hours} for a in upcoming_assignments],
            "weekly_load_hours": weekly_load_hours,
            "weekly_capacity_hours": current_user.weekly_capacity_hours,
            "load_percent": round((weekly_load_hours / current_user.weekly_capacity_hours) * 100, 1) if current_user.weekly_capacity_hours else 0
        },
        "jobs": {
            "overdue_followups": overdue_followups
        },
        "fitness": {
            "days_since_workout": days_since_workout
        },
        "finance": {
            "total_spent": total_spent,
            "monthly_budget": current_user.monthly_budget,
            "budget_percent": budget_percent
        }
    }
