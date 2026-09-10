"""
Dependencies — FastAPI Dependency Injection for Authentication

This module provides the authentication dependency used by all protected endpoints:
- get_current_user: Extracts and validates the JWT token from cookies

This is the core of the auth system — it's injected into every endpoint
that requires authentication via Depends(get_current_user).
"""

from fastapi import Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth import decode_token
from app.models.user import User


def get_current_user(
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts and validates the current user from cookies.
    
    This function is injected into protected endpoints via Depends(get_current_user).
    It:
    1. Reads the access_token from cookies
    2. Decodes and verifies the JWT token
    3. Looks up the user from the database
    4. Returns the user object (or raises 401)
    
    Usage in endpoints:
        @router.get("/protected")
        def protected_endpoint(current_user: User = Depends(get_current_user)):
            return {"user": current_user.name}
    
    Args:
        access_token: JWT token from cookies (auto-extracted by FastAPI)
        db: Database session (injected by Depends)
    
    Returns:
        User object for the authenticated user
    
    Raises:
        HTTPException 401: If not authenticated, token invalid, or user not found
    """
    # Check if token exists
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Decode and verify the JWT token
    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Extract user ID from token payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Look up the user in the database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
