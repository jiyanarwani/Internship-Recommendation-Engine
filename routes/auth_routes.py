from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session, select
from database import get_session
from models import User, Profile
from schemas import RegisterRequest, LoginRequest

auth_router = APIRouter()

@auth_router.post('/register')
def register(payload: RegisterRequest, request: Request, session: Session = Depends(get_session)):
    email = payload.email.strip().lower()
    password = payload.password
    role = payload.role.strip().lower()
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
        
    if role not in ['candidate', 'admin']:
        role = 'candidate'
        
    # Check if user already exists
    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    try:
        user = User(email=email, role=role)
        user.set_password(password)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Auto-create empty profile if they are a candidate
        if role == 'candidate':
            profile = Profile(
                user_id=user.id,
                full_name=email.split('@')[0].capitalize(),
                skills=[],
                interests=[]
            )
            session.add(profile)
            session.commit()
            
        return {"message": "Registration successful. You can now login.", "user_id": user.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@auth_router.post('/login')
def login(payload: LoginRequest, request: Request, session: Session = Depends(get_session)):
    email = payload.email.strip().lower()
    password = payload.password
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
        
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user or not user.check_password(password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    # Store session
    request.session['user_id'] = user.id
    request.session['role'] = user.role
    request.session['logged_in'] = True
    
    # Check profile completion
    profile_completed = False
    full_name = "User"
    if user.role == 'candidate' and user.profile:
        full_name = user.profile.full_name
        p = user.profile
        if p.education_level and p.degree and p.branch and p.skills:
            profile_completed = True

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "name": full_name,
            "profile_completed": profile_completed
        }
    }

@auth_router.post('/logout')
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}

@auth_router.get('/session')
def check_session(request: Request, session: Session = Depends(get_session)):
    user_id = request.session.get('user_id')
    if not user_id:
        return {"logged_in": False}
        
    user = session.get(User, user_id)
    if not user:
        request.session.clear()
        return {"logged_in": False}
        
    profile_completed = False
    full_name = "User"
    if user.role == 'candidate' and user.profile:
        full_name = user.profile.full_name
        p = user.profile
        if p.education_level and p.degree and p.branch and p.skills:
            profile_completed = True
            
    return {
        "logged_in": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "name": full_name,
            "profile_completed": profile_completed
        }
    }
