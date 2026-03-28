from fastapi import Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth import decode_token
from app.models.user import User

def get_current_user(
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user