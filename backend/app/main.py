from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import auth, assignments, jobs, workouts, expenses, dashboard, ai
from app.logger import logger
import uuid
import time

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="LifeOS API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://lifeos-73limfqyh-son-les-projects-e2c594e3.vercel.app",  # ← replace with your actual Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start_time) * 1000)

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