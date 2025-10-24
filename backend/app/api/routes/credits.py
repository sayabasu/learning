from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ...db import get_session
from ...models import CreditSource, CreditTransaction, User, UserRole
from ...schemas import CreditAwardRequest, CreditDonationRequest, CreditTransactionRead
from ..deps import get_current_active_user, log_activity, require_roles

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/me", response_model=List[CreditTransactionRead])
def list_my_transactions(
    session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user)
) -> List[CreditTransaction]:
    statement = select(CreditTransaction).where(CreditTransaction.user_id == current_user.id)
    return session.exec(statement).all()


@router.post(
    "/donate",
    response_model=CreditTransactionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.SPONSOR))],
)
def donate_credits(
    donation: CreditDonationRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> CreditTransaction:
    if donation.amount <= 0:
        raise HTTPException(status_code=400, detail="Donation amount must be positive")
    transaction = CreditTransaction(
        user_id=current_user.id,
        amount=donation.amount,
        source=CreditSource.SPONSOR,
        description=donation.description,
    )
    session.add(transaction)
    session.flush()
    session.refresh(transaction)
    log_activity(
        session,
        actor_id=current_user.id,
        action="donate_credits",
        entity_type="credit_transaction",
        entity_id=transaction.id,
        details=f"Donated {donation.amount} credits",
    )
    session.commit()
    return transaction


@router.post(
    "/award",
    response_model=CreditTransactionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.COACH, UserRole.ADMIN))],
)
def award_credits(
    award: CreditAwardRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> CreditTransaction:
    if award.amount <= 0:
        raise HTTPException(status_code=400, detail="Award amount must be positive")
    student = session.get(User, award.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    transaction = CreditTransaction(
        user_id=award.student_id,
        amount=award.amount,
        source=CreditSource.COACH if current_user.role == UserRole.COACH else CreditSource.SYSTEM,
        description=award.description,
    )
    session.add(transaction)
    session.flush()
    session.refresh(transaction)
    log_activity(
        session,
        actor_id=current_user.id,
        action="award_credits",
        entity_type="credit_transaction",
        entity_id=transaction.id,
        details=f"Awarded {award.amount} credits to {student.full_name}",
    )
    session.commit()
    return transaction
