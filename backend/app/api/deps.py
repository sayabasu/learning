from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session, select

from ..core.security import decode_access_token
from ..db import get_session
from ..models import ActivityLog, User, UserRole
from ..schemas import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        token_data = TokenPayload.model_validate(payload)
    except JWTError as exc:  # pragma: no cover - defensive branch
        raise credentials_exception from exc
    if token_data.sub is None:
        raise credentials_exception
    user = session.get(User, int(token_data.sub))
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def log_activity(
    session: Session,
    *,
    actor_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: str | None = None,
) -> ActivityLog:
    entry = ActivityLog(actor_id=actor_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details)
    session.add(entry)
    session.flush()
    session.refresh(entry)
    return entry


def get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()
