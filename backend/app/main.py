from fastapi import FastAPI
from app.routers import auth, assignments, jobs, workouts, expenses, dashboard

app = FastAPI(title="LifeOS API")

app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(jobs.router)
app.include_router(workouts.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)

@app.get("/health")
def health():
    return {"status": "ok"}