from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from ...core.security import create_access_token, get_password_hash, verify_password
from ...db import get_session
from ...models import User, UserRole
from ...schemas import Token, UserCreate, UserRead
from ..deps import get_user_by_email, log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, session: Session = Depends(get_session)) -> User:
    existing_user = get_user_by_email(session, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        role=UserRole.STUDENT,
        hashed_password=get_password_hash(user_in.password),
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    log_activity(
        session,
        actor_id=user.id,
        action="register",
        entity_type="user",
        entity_id=user.id,
        details="New student registration",
    )
    session.commit()
    return user


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)
) -> Token:
    user = get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    access_token = create_access_token(str(user.id))
    log_activity(
        session,
        actor_id=user.id,
        action="login",
        entity_type="user",
        entity_id=user.id,
        details="User authenticated",
    )
    session.commit()
    return Token(access_token=access_token)
