from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, assignments, jobs, workouts, expenses, dashboard, ai
from app.logger import logger
import uuid

app = FastAPI(title="LifeOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-vercel-url.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = __import__("time").time()
    response = await call_next(request)
    latency_ms = round((__import__("time").time() - start_time) * 1000)
    
    if response.status_code >= 400:
        logger.error(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms
        )
    else:
        logger.info(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms
        )
    
    return response

app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(jobs.router)
app.include_router(workouts.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(ai.router)

@app.get("/health")
def health():
    return {"status": "ok"}