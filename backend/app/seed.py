import uuid
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense, ExpenseCategory
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

    # Assignments
    assignments = [
        Assignment(id=uuid.uuid4(), user_id=user.id, title="CS Final Project", course="CS320", due_date=now + timedelta(days=3), estimated_hours=10, status=AssignmentStatus.pending),
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Economics Essay", course="ECON210", due_date=now + timedelta(days=5), estimated_hours=4, status=AssignmentStatus.pending),
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Math Problem Set", course="MATH301", due_date=now + timedelta(days=7), estimated_hours=3, status=AssignmentStatus.pending),
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Data Structures HW", course="CS220", due_date=now - timedelta(days=2), estimated_hours=2, status=AssignmentStatus.done),
        Assignment(id=uuid.uuid4(), user_id=user.id, title="Physics Lab Report", course="PHYS101", due_date=now - timedelta(days=5), estimated_hours=3, status=AssignmentStatus.done),
    ]
    db.add_all(assignments)

    # Job applications
    jobs = [
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Google", role="SWE Intern", applied_date=(now - timedelta(days=14)).date(), status=JobStatus.interview, followup_date=(now - timedelta(days=7)).date()),
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Meta", role="SWE Intern", applied_date=(now - timedelta(days=10)).date(), status=JobStatus.applied, followup_date=(now - timedelta(days=3)).date()),
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Apple", role="ML Intern", applied_date=(now - timedelta(days=7)).date(), status=JobStatus.applied, followup_date=(now).date()),
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Amazon", role="SDE Intern", applied_date=(now - timedelta(days=20)).date(), status=JobStatus.rejected, followup_date=(now - timedelta(days=13)).date()),
        JobApplication(id=uuid.uuid4(), user_id=user.id, company="Microsoft", role="SWE Intern", applied_date=(now - timedelta(days=3)).date(), status=JobStatus.applied, followup_date=(now + timedelta(days=4)).date()),
    ]
    db.add_all(jobs)

    # Workouts
    workouts = [
        Workout(id=uuid.uuid4(), user_id=user.id, type="Run", duration_mins=30, logged_at=now - timedelta(days=1)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Gym", duration_mins=60, logged_at=now - timedelta(days=3)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Yoga", duration_mins=45, logged_at=now - timedelta(days=5)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Run", duration_mins=25, logged_at=now - timedelta(days=7)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Gym", duration_mins=55, logged_at=now - timedelta(days=10)),
        Workout(id=uuid.uuid4(), user_id=user.id, type="Basketball", duration_mins=90, logged_at=now - timedelta(days=14)),
    ]
    db.add_all(workouts)

    # Expenses
    expenses = [
        Expense(id=uuid.uuid4(), user_id=user.id, amount=12.50, category=ExpenseCategory.food, note="Lunch", spent_at=now - timedelta(days=1)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=45.00, category=ExpenseCategory.food, note="Groceries", spent_at=now - timedelta(days=3)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=8.00, category=ExpenseCategory.transport, note="Uber", spent_at=now - timedelta(days=4)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=25.00, category=ExpenseCategory.study, note="Textbook", spent_at=now - timedelta(days=6)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=15.00, category=ExpenseCategory.fitness, note="Gym day pass", spent_at=now - timedelta(days=8)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=30.00, category=ExpenseCategory.food, note="Dinner with friends", spent_at=now - timedelta(days=10)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=18.00, category=ExpenseCategory.transport, note="Bus pass", spent_at=now - timedelta(days=12)),
        Expense(id=uuid.uuid4(), user_id=user.id, amount=22.00, category=ExpenseCategory.food, note="Coffee + snacks", spent_at=now - timedelta(days=14)),
    ]
    db.add_all(expenses)

    db.commit()
    db.close()
    print("✅ Demo account seeded successfully!")
    print("   Email: demo@lifeos.app")
    print("   Password: demo1234")

if __name__ == "__main__":
    seed()