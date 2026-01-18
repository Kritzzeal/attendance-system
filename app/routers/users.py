# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import models, schemas, auth
from ..database import get_db
from fastapi.security import OAuth2PasswordBearer  # ADD IF MISSING

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        teacher_id=user.teacher_id,
        role=user.role,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    # Authenticate
    db_user = auth.authenticate_user(db, email=user.email, password=user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = auth.create_access_token(data={"user_id": db_user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/create-admin")
def create_admin(db: Session = Depends(get_db)):
    # Check if admin exists
    admin = db.query(models.User).filter(models.User.role == "admin").first()
    if admin:
        return {"message": "Admin already exists"}
    
    # Create admin
    hashed_password = auth.get_password_hash("admin123")
    admin_user = models.User(
        email="admin@college.com",
        name="Admin",
        teacher_id="ADMIN001",
        role="admin",
        hashed_password=hashed_password
    )
    
    db.add(admin_user)
    db.commit()
    return {
        "message": "Admin created",
        "email": "admin@college.com",
        "password": "admin123",
        "warning": "Change password!"
    }
# Add to app/routers/users.py
@router.get("/me", response_model=schemas.UserResponse)
def get_current_user(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info"""
    return current_user