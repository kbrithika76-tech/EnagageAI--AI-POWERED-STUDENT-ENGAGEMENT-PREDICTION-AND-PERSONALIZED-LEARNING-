"""
EngageAI Backend — routes/auth.py
POST /auth/login
POST /auth/register
GET  /auth/me
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.database import get_db
from backend.models.user import User
from backend.auth.password import hash_password, verify_password
from backend.auth.jwt import create_access_token
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email   : EmailStr
    password: str


class RegisterRequest(BaseModel):
    name    : str
    email   : EmailStr
    password: str
    role    : str = "student"


class TokenResponse(BaseModel):
    access_token: str
    token_type  : str = "bearer"
    user_id     : int
    name        : str
    email       : str
    role        : str


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive.")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    role = body.role if body.role in ("student", "teacher", "admin") else "student"
    user = User(
        name          = body.name,
        email         = body.email,
        password_hash = hash_password(body.password),
        role          = role,
        created_at    = datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id"      : current_user.id,
        "name"    : current_user.name,
        "email"   : current_user.email,
        "role"    : current_user.role,
        "profile" : current_user.profile,
    }
