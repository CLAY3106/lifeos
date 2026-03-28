from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, LoginRequest, Token
from app.services.auth import hash_password, authenticate_user, create_access_token
from app.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    # check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # create new user
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        name=user_data.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # create token and set cookie
    token = create_access_token({"sub": str(new_user.id)})
    response.set_cookie(key="access_token", value=token, httponly=True)

    return new_user

@router.post("/login")
def login(credentials: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(user.id)})
    response.set_cookie(key="access_token", value=token, httponly=True)
    
    return {"message": "Login successful", "user": UserResponse.model_validate(user)}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user