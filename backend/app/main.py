"""
LifeOS API — Main Application Entry Point

This module configures and runs the FastAPI application:
1. Middleware — CORS, request logging, rate limiting
2. Routers — All API endpoints
3. Health checks — Database connectivity

The app uses:
- FastAPI for the web framework
- CORS for cross-origin requests (localhost + Vercel)
- SlowAPI for rate limiting (per IP address)
- Structured logging for request tracking
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import auth, assignments, jobs, workouts, expenses, dashboard, ai, routines, activity
from app.database import check_db_connection
from app.logger import logger
import uuid
import time

# Rate limiter — limits requests per IP address
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI application
app = FastAPI(title="LifeOS API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware — allows cross-origin requests from:
# - localhost:3000 (local development)
# - lifeos-lac.vercel.app (production frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://lifeos-lac.vercel.app",
    ],
    allow_credentials=True,  # Allow cookies
    allow_methods=["*"],     # Allow all HTTP methods
    allow_headers=["*"],     # Allow all headers
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware that logs every HTTP request.
    
    Logs:
    - request_id: Unique ID for tracing
    - method: HTTP method (GET, POST, etc.)
    - path: Request path
    - status_code: Response status code
    - latency_ms: Request duration in milliseconds
    
    Errors (status_code >= 400) are logged as errors,
    successful requests are logged as info.
    """
    request_id = str(uuid.uuid4())[:8]  # Short ID for readability
    start_time = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start_time) * 1000)

    # Log errors separately for alerting
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


# Register all API routers
app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(jobs.router)
app.include_router(workouts.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(routines.router)
app.include_router(activity.router)


@app.get("/health")
def health():
    """Basic health check endpoint."""
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    """Database connectivity health check."""
    return check_db_connection()
