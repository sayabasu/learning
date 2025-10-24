from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ...core.security import get_password_hash
from ...db import get_session
from ...models import User, UserRole
from ...schemas import Message, UserCreateWithRole, UserRead, UserUpdate
from ..deps import get_current_active_user, get_user_by_email, log_activity, require_roles

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@router.get("", response_model=list[UserRead], dependencies=[Depends(require_roles(UserRole.ADMIN))])
def list_users(session: Session = Depends(get_session)) -> list[User]:
    return session.query(User).all()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def create_user(user_in: UserCreateWithRole, session: Session = Depends(get_session)) -> User:
    if get_user_by_email(session, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        role=user_in.role,
        hashed_password=get_password_hash(user_in.password),
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    log_activity(
        session,
        actor_id=None,
        action="create_user",
        entity_type="user",
        entity_id=user.id,
        details=f"User created with role {user.role}",
    )
    session.commit()
    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def update_user(user_id: int, user_in: UserUpdate, session: Session = Depends(get_session)) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    session.add(user)
    session.flush()
    session.refresh(user)
    log_activity(
        session,
        actor_id=None,
        action="update_user",
        entity_type="user",
        entity_id=user.id,
        details="User updated",
    )
    session.commit()
    return user


@router.delete(
    "/{user_id}",
    response_model=Message,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def deactivate_user(user_id: int, session: Session = Depends(get_session)) -> Message:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    session.add(user)
    session.flush()
    log_activity(
        session,
        actor_id=None,
        action="deactivate_user",
        entity_type="user",
        entity_id=user.id,
        details="User deactivated",
    )
    session.commit()
    return Message(message="User deactivated")
