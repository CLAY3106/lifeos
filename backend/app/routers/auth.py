"""
Auth Router — User Registration, Login, Logout, and Profile Management

This module handles authentication endpoints:
1. POST /register — Create new user account
2. POST /login — Authenticate and set JWT cookie
3. POST /logout — Clear JWT cookie
4. GET /me — Get current user profile
5. PATCH /me — Update current user profile

Security notes:
- Passwords are hashed with Bcrypt before storage
- JWT tokens are stored in httponly cookies (not accessible via JavaScript)
- Cookies use SameSite=None and Secure=True for cross-origin requests
- Token expiry is 7 days (configurable via ACCESS_TOKEN_EXPIRE_DAYS)
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate, LoginRequest, Token
from app.services.auth import hash_password, verify_password, authenticate_user, create_access_token
from app.dependencies import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse)
@limiter.limit("3/minute")
def register(request: Request, user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user with:
    - Email (must be unique)
    - Password (hashed with Bcrypt)
    - Name
    
    After registration, automatically logs in the user by setting
    the JWT cookie.
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        name=user_data.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create token and set cookie (auto-login after registration)
    token = create_access_token({"sub": str(new_user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,      # Not accessible via JavaScript (XSS protection)
        samesite="none",    # Allow cross-origin requests
        secure=True         # Only send over HTTPS
    )

    return new_user


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, credentials: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate a user and set JWT cookie.
    
    The cookie is set with:
    - httponly=True: Not accessible via JavaScript (XSS protection)
    - samesite="none": Allow cross-origin requests
    - secure=True: Only send over HTTPS
    """
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="none",
        secure=True
    )
    
    return {"message": "Login successful", "user": UserResponse.model_validate(user)}


@router.post("/logout")
def logout(response: Response):
    """
    Log out a user by clearing the JWT cookie.
    
    The client-side should also clear any cached user data.
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    
    Requires a valid JWT token in cookies.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the current user's profile.
    
    Supports updating:
    - Name
    - Monthly budget
    - Weekly capacity hours
    - Password (requires current password verification)
    
    If updating password, the current password must be provided
    and verified before the new password is set.
    """
    if data.name is not None:
        current_user.name = data.name
    if data.monthly_budget is not None:
        current_user.monthly_budget = data.monthly_budget
    if data.weekly_capacity_hours is not None:
        current_user.weekly_capacity_hours = data.weekly_capacity_hours

    # Password change requires current password verification
    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Current password required")
        if not verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        current_user.hashed_password = hash_password(data.new_password)

    db.commit()
    db.refresh(current_user)
    return current_user
