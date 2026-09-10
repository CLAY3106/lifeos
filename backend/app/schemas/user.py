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

from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


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
    
    Note: password hash is never included in responses.
    
    Config: from_attributes = True allows creating from SQLAlchemy models.
    """
    id: UUID
    email: str
    name: str | None = None
    monthly_budget: float = 200
    weekly_capacity_hours: float = 40

    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    
    All fields are optional — only provided fields are updated.
    Password changes require current_password verification.
    """
    name: Optional[str] = None
    monthly_budget: Optional[float] = None
    weekly_capacity_hours: Optional[float] = None
    current_password: Optional[str] = None  # Required for password change
    new_password: Optional[str] = None


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
