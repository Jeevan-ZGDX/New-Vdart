from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.database import get_db
from talkcraft_coach.database.models import User
from talkcraft_coach.auth.auth_handler import auth_handler
from talkcraft_coach.auth.auth_middleware import require_auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., max_length=128)
    password: str = Field(..., min_length=6, max_length=128)
    display_name: str = Field(default="", max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    skill_level: str
    total_sessions: int
    total_practice_time_minutes: int


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: DbSession = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == req.username) | (User.email == req.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=auth_handler.hash_password(req.password),
        display_name=req.display_name or req.username,
        skill_level="beginner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = auth_handler.create_access_token(user.id, user.username)
    refresh_token = auth_handler.create_refresh_token(user.id)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "skill_level": user.skill_level,
        },
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: DbSession = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not auth_handler.verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = auth_handler.create_access_token(user.id, user.username)
    refresh_token = auth_handler.create_refresh_token(user.id)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "skill_level": user.skill_level,
        },
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user_data: dict = Depends(require_auth), db: DbSession = Depends(get_db)):
    user = db.query(User).filter(User.id == user_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name or user.username,
        skill_level=user.skill_level or "beginner",
        total_sessions=user.total_sessions or 0,
        total_practice_time_minutes=user.total_practice_time_minutes or 0,
    )


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: DbSession = Depends(get_db)):
    payload = auth_handler.decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    access = auth_handler.create_access_token(user.id, user.username)
    return {"access_token": access, "token_type": "bearer"}
