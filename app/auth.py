import uuid
from typing import Iterable

from fastapi import Depends, Header, HTTPException, status
from passlib.context import CryptContext
from sqlmodel import Session, select

from .database import get_session
from .models import SessionToken, User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_session_token(user_id: int, session: Session) -> str:
    token = uuid.uuid4().hex
    session.add(SessionToken(token=token, user_id=user_id))
    session.commit()
    return token


def get_user_from_token(token: str, session: Session) -> User:
    statement = select(SessionToken).where(SessionToken.token == token)
    token_row = session.exec(statement).first()
    if not token_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = session.get(User, token_row.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user(token: str = Header(..., alias="X-Token"), session: Session = Depends(get_session)) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return get_user_from_token(token, session)


class RoleChecker:
    def __init__(self, allowed_roles: Iterable[UserRole]):
        self.allowed_roles = set(allowed_roles)

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user


def require_roles(*roles: UserRole) -> RoleChecker:
    return RoleChecker(roles)
