from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ...db import get_session
from ...models import Quiz, QuizAttempt, QuizQuestion, User, UserRole
from ...schemas import QuizAttemptCreate, QuizAttemptRead, QuizQuestionRead, QuizRead
from ..deps import get_current_active_user, log_activity, require_roles

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("/{quiz_id}", response_model=QuizRead)
def get_quiz(quiz_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user)) -> QuizRead:
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    questions = session.exec(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)).all()
    return QuizRead(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        created_at=quiz.created_at,
        questions=[QuizQuestionRead.model_validate(question, from_attributes=True) for question in questions],
    )


@router.post(
    "/{quiz_id}/attempts",
    response_model=QuizAttemptRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
def submit_quiz_attempt(
    quiz_id: int,
    attempt: QuizAttemptCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> QuizAttempt:
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    questions = session.exec(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)).all()
    if len(attempt.responses) != len(questions):
        raise HTTPException(status_code=400, detail="Responses count does not match quiz questions")
    total_correct = sum(1 for response, question in zip(attempt.responses, questions) if response == question.answer_index)
    score = (total_correct / len(questions)) * 100 if questions else 0.0
    quiz_attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=current_user.id,
        score=score,
        responses=attempt.responses,
    )
    session.add(quiz_attempt)
    session.flush()
    session.refresh(quiz_attempt)
    log_activity(
        session,
        actor_id=current_user.id,
        action="submit_quiz",
        entity_type="quiz_attempt",
        entity_id=quiz_attempt.id,
        details=f"Quiz attempted with score {score:.2f}",
    )
    session.commit()
    return quiz_attempt
