"""
Auth Service — Password Hashing, JWT Tokens, and User Authentication

This module handles authentication logic:
1. Password hashing — Bcrypt for secure password storage
2. JWT tokens — Access tokens with 7-day expiry
3. User lookup — Find users by email
4. Authentication — Verify credentials

Security notes:
- Passwords are hashed with Bcrypt (salted, one-way)
- JWT tokens are signed with a secret key (HS256)
- Tokens expire after 7 days (configurable via ACCESS_TOKEN_EXPIRE_DAYS)
- The secret key is loaded from JWT_SECRET env var (defaults to dev key)
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user import User
import os

# Configuration — loaded from environment variables
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"  # HMAC-SHA256 for JWT signing
ACCESS_TOKEN_EXPIRE_DAYS = 7  # Token validity period

# Bcrypt context for password hashing
# "deprecated="auto"" means it will warn if bcrypt is deprecated
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using Bcrypt.
    
    Bcrypt automatically generates a salt and hashes the password.
    The output includes the salt, so you don't need to store it separately.
    
    Args:
        password: Plain text password to hash
    
    Returns:
        Bcrypt hash string (includes salt)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a Bcrypt hash.
    
    Args:
        plain_password: The password the user entered
        hashed_password: The stored hash from the database
    
    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    
    The token contains:
    - The data payload (typically {"sub": user_id})
    - An expiration time (7 days from now)
    
    Args:
        data: Payload to encode in the token (e.g., {"sub": user_id})
    
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT string to decode
    
    Returns:
        Decoded payload dict, or None if token is invalid/expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_by_email(db: Session, email: str) -> User:
    """
    Find a user by their email address.
    
    Args:
        db: Database session
        email: User's email address
    
    Returns:
        User object, or None if not found
    """
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate a user with email and password.
    
    This function:
    1. Looks up the user by email
    2. Verifies the password against the stored hash
    3. Returns the user if successful, None otherwise
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
    
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
