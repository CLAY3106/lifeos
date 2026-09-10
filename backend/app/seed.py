import uuid
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus, JobStatusHistory
from app.models.workout import Workout
from app.models.expense import Expense, ExpenseCategory
from app.models.routine import Routine, RoutineItem, RoutineDayOfWeek
from app.models.activity_log import ActivityLog
from app.models.ai_insight import AIInsight
from app.models.ai_usage_log import AIUsageLog
from app.services.auth import hash_password


def seed():
    db = SessionLocal()

    # Check if demo user already exists
    existing = db.query(User).filter(User.email == "demo@lifeos.app").first()
    if existing:
        print("Demo user already exists — skipping seed")
        db.close()
        return

    now = datetime.now(timezone.utc)

    # Create demo user
    user = User(
        id=uuid.uuid4(),
        email="demo@lifeos.app",
        hashed_password=hash_password("demo1234"),
        name="Alex",
        monthly_budget=300,
        weekly_capacity_hours=40
    )
    db.add(user)
    db.flush()

    # ── Assignments ──────────────────────────────────────────────
    # Mix of urgent, upcoming, and completed
    assignments = [
        # Urgent — due within 2 days
        Assignment(id=uuid.uuid4(), user_id=user.id, title="CS Final Project", course="CS320",
                   due_date=now + timedelta(days=1), estimated_hours=8, status=AssignmentStatus.pending),
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Econ Essay Draft", course="ECON210",
                   due_date=now + timedelta(days=2), estimated_hours=4, status=AssignmentStatus.pending),
        # This week
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Math Problem Set 7", course="MATH301",
                   due_date=now + timedelta(days=5), estimated_hours=3, status=AssignmentStatus.pending),
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Physics Lab Report", course="PHYS101",
                   due_date=now + timedelta(days=6), estimated_hours=2, status=AssignmentStatus.pending),
        # Next week
        Assignment(id=uuid.uuid4(), user_id=user.id, title="ML Model Training", course="CS480",
                   due_date=now + timedelta(days=12), estimated_hours=6, status=AssignmentStatus.pending),
        # Done
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Data Structures HW", course="CS220",
                   due_date=now - timedelta(days=3), estimated_hours=2, status=AssignmentStatus.done),
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Microeconomics Quiz", course="ECON210",
                   due_date=now - timedelta(days=7), estimated_hours=1, status=AssignmentStatus.done),
    ]
    db.add_all(assignments)

    # ── Job Applications ─────────────────────────────────────────
    # Different stages of the pipeline
    jobs = [
        # Interview stage
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Google", role="SWE Intern",
                       applied_date=(now - timedelta(days=21)).date(),
                       status=JobStatus.interview_scheduled,
                       followup_date=(now - timedelta(days=5)).date(),
                       location="Mountain View, CA"),
        # Applied, waiting
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Meta", role="SWE Intern",
                       applied_date=(now - timedelta(days=14)).date(),
                       status=JobStatus.applied,
                       followup_date=(now + timedelta(days=2)).date(),
                       location="Menlo Park, CA"),
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Apple", role="ML Intern",
                       applied_date=(now - timedelta(days=10)).date(),
                       status=JobStatus.applied,
                       followup_date=(now + timedelta(days=5)).date(),
                       location="Cupertino, CA"),
        # Just applied
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Microsoft", role="SWE Intern",
                       applied_date=(now - timedelta(days=3)).date(),
                       status=JobStatus.applied,
                       followup_date=(now + timedelta(days=7)).date(),
                       location="Redmond, WA"),
        # Rejected
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Amazon", role="SDE Intern",
                       applied_date=(now - timedelta(days=30)).date(),
                       status=JobStatus.rejected,
                       followup_date=(now - timedelta(days=20)).date(),
                       location="Seattle, WA"),
    ]
    db.add_all(jobs)

    # ── Workouts ─────────────────────────────────────────────────
    # Regular workout streak (last 2 weeks)
    workouts = [
        Workout(id=uuid.uuid4(), user_id=user.id, type="Strength", duration_mins=55,
                notes="Upper body — bench, rows, OHP", logged_at=now - timedelta(days=0)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Run", duration_mins=32,
                notes="5K easy pace", logged_at=now - timedelta(days=1)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Strength", duration_mins=60,
                notes="Legs — squats, RDL, leg press", logged_at=now - timedelta(days=2)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Yoga", duration_mins=40,
                notes="Recovery session", logged_at=now - timedelta(days=4)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Run", duration_mins=45,
                notes="Interval training", logged_at=now - timedelta(days=5)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Strength", duration_mins=50,
                notes="Push day", logged_at=now - timedelta(days=7)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Basketball", duration_mins=90,
                notes="Pickup game at campus court", logged_at=now - timedelta(days=9)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Run", duration_mins=25,
                notes="Morning jog", logged_at=now - timedelta(days=11)),
    ]
    db.add_all(workouts)

    # ── Expenses (current month — for envelopes) ─────────────────
    # Use group_override to explicitly mark need vs want
    current_month_expenses = [
        # Needs
        Expense(id=uuid.uuid4(), user_id=user.id, amount=42.50, category=ExpenseCategory.food,
                group_override="needs", note="Weekly groceries",
                spent_at=now - timedelta(days=1)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=8.50, category=ExpenseCategory.transport,
                group_override="needs", note="Metro card reload",
                spent_at=now - timedelta(days=2)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=65.00, category=ExpenseCategory.study,
                group_override="needs", note="CS textbook",
                spent_at=now - timedelta(days=3)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=15.00, category=ExpenseCategory.food,
                group_override="needs", note="Groceries — snacks for study",
                spent_at=now - timedelta(days=5)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=12.00, category=ExpenseCategory.transport,
                group_override="needs", note="Bus to campus",
                spent_at=now - timedelta(days=6)),
        # Wants
        Expense(id=uuid.uuid4(), user_id=user.id, amount=35.00, category=ExpenseCategory.food,
                group_override="wants", note="Dinner with friends",
                spent_at=now - timedelta(days=2)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=14.00, category=ExpenseCategory.food,
                group_override="wants", note="Coffee shop study session",
                spent_at=now - timedelta(days=4)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=25.00, category=ExpenseCategory.fitness,
                group_override="wants", note="Day pass — different gym",
                spent_at=now - timedelta(days=7)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=18.00, category=ExpenseCategory.transport,
                group_override="wants", note="Uber to party",
                spent_at=now - timedelta(days=5)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=22.00, category=ExpenseCategory.other,
                group_override="wants", note="Concert tickets",
                spent_at=now - timedelta(days=8)),
    ]
    db.add_all(current_month_expenses)

    # ── Expenses (previous months — for transaction history) ─────
    last_month_expenses = [
        Expense(id=uuid.uuid4(), user_id=user.id, amount=55.00, category=ExpenseCategory.food,
                group_override="needs", note="Groceries",
                spent_at=now - timedelta(days=35)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=30.00, category=ExpenseCategory.food,
                group_override="wants", note="Birthday dinner",
                spent_at=now - timedelta(days=38)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=20.00, category=ExpenseCategory.transport,
                group_override="needs", note="Monthly bus pass",
                spent_at=now - timedelta(days=40)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=45.00, category=ExpenseCategory.study,
                group_override="needs", note="Course materials",
                spent_at=now - timedelta(days=42)),
    ]
    db.add_all(last_month_expenses)

    # ── Routines ─────────────────────────────────────────────────
    push_pull = Routine(id=uuid.uuid4(), user_id=user.id, name="Push / Pull")
    db.add(push_pull)
    db.flush()

    push_pull_items = [
        RoutineItem(id=uuid.uuid4(), routine_id=push_pull.id, exercise_name="Bench Press",
                    sets=4, reps=8, day_of_week=RoutineDayOfWeek.monday, order_index=0),
        RoutineItem(id=uuid.uuid4(), routine_id=push_pull.id, exercise_name="Overhead Press",
                    sets=3, reps=10, day_of_week=RoutineDayOfWeek.monday, order_index=1),
        RoutineItem(id=uuid.uuid4(), routine_id=push_pull.id, exercise_name="Dumbbell Rows",
                    sets=4, reps=8, day_of_week=RoutineDayOfWeek.thursday, order_index=2),
        RoutineItem(id=uuid.uuid4(), routine_id=push_pull.id, exercise_name="Pull-ups",
                    sets=3, reps=10, day_of_week=RoutineDayOfWeek.thursday, order_index=3),
    ]
    db.add_all(push_pull_items)

    leg_day = Routine(id=uuid.uuid4(), user_id=user.id, name="Leg Day")
    db.add(leg_day)
    db.flush()

    leg_day_items = [
        RoutineItem(id=uuid.uuid4(), routine_id=leg_day.id, exercise_name="Squats",
                    sets=5, reps=5, day_of_week=RoutineDayOfWeek.tuesday, order_index=0),
        RoutineItem(id=uuid.uuid4(), routine_id=leg_day.id, exercise_name="Romanian Deadlift",
                    sets=3, reps=10, day_of_week=RoutineDayOfWeek.tuesday, order_index=1),
        RoutineItem(id=uuid.uuid4(), routine_id=leg_day.id, exercise_name="Leg Press",
                    sets=3, reps=12, day_of_week=RoutineDayOfWeek.tuesday, order_index=2),
        RoutineItem(id=uuid.uuid4(), routine_id=leg_day.id, exercise_name="Calf Raises",
                    sets=4, reps=15, day_of_week=RoutineDayOfWeek.friday, order_index=3),
    ]
    db.add_all(leg_day_items)

    cardio = Routine(id=uuid.uuid4(), user_id=user.id, name="Cardio")
    db.add(cardio)
    db.flush()

    cardio_items = [
        RoutineItem(id=uuid.uuid4(), routine_id=cardio.id, exercise_name="5K Run",
                    duration_mins=30, day_of_week=RoutineDayOfWeek.wednesday, order_index=0),
        RoutineItem(id=uuid.uuid4(), routine_id=cardio.id, exercise_name="Jump Rope",
                    duration_mins=15, day_of_week=RoutineDayOfWeek.wednesday, order_index=1),
    ]
    db.add_all(cardio_items)

    db.commit()
    db.close()
    print("Demo account seeded successfully!")
    print("   Email: demo@lifeos.app")
    print("   Password: demo1234")


def reset_and_seed():
    """Delete all demo user data and re-seed. Use for development."""
    db = SessionLocal()
    user = db.query(User).filter(User.email == "demo@lifeos.app").first()
    if user:
        # Delete in order (foreign keys)
        db.query(ActivityLog).filter(ActivityLog.user_id == user.id).delete()
        db.query(AIUsageLog).filter(AIUsageLog.user_id == user.id).delete()
        db.query(AIInsight).filter(AIInsight.user_id == user.id).delete()
        db.query(JobStatusHistory).filter(
            JobStatusHistory.job_id.in_(
                db.query(JobApplication.id).filter(JobApplication.user_id == user.id)
            )
        ).delete(synchronize_session=False)
        db.query(RoutineItem).filter(
            RoutineItem.routine_id.in_(
                db.query(Routine.id).filter(Routine.user_id == user.id)
            )
        ).delete(synchronize_session=False)
        db.query(Routine).filter(Routine.user_id == user.id).delete()
        db.query(Assignment).filter(Assignment.user_id == user.id).delete()
        db.query(JobApplication).filter(JobApplication.user_id == user.id).delete()
        db.query(Workout).filter(Workout.user_id == user.id).delete()
        db.query(Expense).filter(Expense.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        print("Demo user deleted")
    db.close()
    seed()


if __name__ == "__main__":
    reset_and_seed()
