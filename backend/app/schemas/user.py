from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    monthly_budget: float = 200
    weekly_capacity_hours: float = 40

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    monthly_budget: Optional[float] = None
    weekly_capacity_hours: Optional[float] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"