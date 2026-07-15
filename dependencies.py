from fastapi import Request, HTTPException, Depends
from sqlmodel import Session
from database import get_session
from models import User

def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = session.get(User, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

def get_current_candidate(user: User = Depends(get_current_user)) -> User:
    if user.role != "candidate":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user

def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
