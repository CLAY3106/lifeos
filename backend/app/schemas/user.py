"""
User Schemas — Request/Response Validation

This module defines Pydantic models for user operations:
1. UserCreate: Register a new user
2. UserResponse: Return user data
3. UserUpdate: Update user profile
4. LoginRequest: Login credentials
5. Token: JWT token response

These schemas validate incoming requests and serialize responses,
ensuring type safety and consistent API contracts.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional

from app.models.user import DEFAULT_ACTIVE_MODULES

# Module keys accepted by PATCH /auth/me for active_modules. Anything else
# is rejected with a 400 instead of being persisted.
ALLOWED_ACTIVE_MODULES = set(DEFAULT_ACTIVE_MODULES)


class UserCreate(BaseModel):
    """
    Schema for registering a new user.
    
    Required fields:
    - email: Valid email address
    - password: Plain text password (hashed before storage)
    
    Optional fields:
    - name: Display name
    """
    email: EmailStr
    password: str
    name: str | None = None


class UserResponse(BaseModel):
    """
    Schema for returning user data.
    
    Includes:
    - All user fields
    - monthly_budget: For finance calculations (default: 200)
    - weekly_capacity_hours: For workload calculations (default: 40)
    - onboarding_completed_at: Timestamp when the onboarding wizard finished
    - active_modules: Enabled module keys (default: all four)
    
    Note: password hash is never included in responses.
    
    Config: from_attributes = True allows creating from SQLAlchemy models.
    """
    id: UUID
    email: str
    name: str | None = None
    monthly_budget: float = 200
    weekly_capacity_hours: float = 40
    onboarding_completed_at: datetime | None = None
    active_modules: list[str] = Field(
        default_factory=lambda: list(DEFAULT_ACTIVE_MODULES)
    )

    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    
    All fields are optional — only provided fields are updated.
    Password changes require current_password verification.
    
    active_modules validation happens in the router so failures return 400:
    non-empty, each value in ALLOWED_ACTIVE_MODULES, duplicates stripped.
    """
    name: Optional[str] = None
    monthly_budget: Optional[float] = None
    weekly_capacity_hours: Optional[float] = None
    current_password: Optional[str] = None  # Required for password change
    new_password: Optional[str] = None
    onboarding_completed_at: Optional[datetime] = None
    active_modules: Optional[list[str]] = None


class LoginRequest(BaseModel):
    """
    Schema for login credentials.
    
    Required fields:
    - email: User's email address
    - password: Plain text password
    """
    email: EmailStr
    password: str


class Token(BaseModel):
    """
    Schema for JWT token response.
    
    Used when returning tokens (though we use cookies instead).
    """
    access_token: str
    token_type: str = "bearer"
