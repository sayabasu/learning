from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from ...db import get_session
from ...models import (
    Course,
    CourseStatus,
    Lesson,
    LessonStatus,
    Notification,
    Quiz,
    QuizQuestion,
    User,
    UserRole,
)
from ...schemas import (
    CourseCreate,
    CourseDetail,
    CourseRead,
    LessonCreate,
    LessonRead,
    QuizCreate,
    QuizQuestionRead,
    QuizRead,
)
from ..deps import get_current_active_user, log_activity, require_roles

router = APIRouter(prefix="/courses", tags=["courses"])


def _create_notification(session: Session, user_id: int, message: str) -> Notification:
    notification = Notification(user_id=user_id, message=message)
    session.add(notification)
    session.flush()
    session.refresh(notification)
    return notification


@router.get("", response_model=List[CourseRead])
def list_courses(
    status_filter: CourseStatus | None = Query(None, alias="status"), session: Session = Depends(get_session)
) -> List[Course]:
    statement = select(Course)
    if status_filter:
        statement = statement.where(Course.status == status_filter)
    else:
        statement = statement.where(Course.status == CourseStatus.PUBLISHED)
    statement = statement.order_by(Course.created_at.desc())
    return session.exec(statement).all()


@router.post(
    "",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.CONTENT_CREATOR, UserRole.ADMIN))],
)
def create_course(
    course_in: CourseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Course:
    course = Course(
        title=course_in.title,
        description=course_in.description,
        subject=course_in.subject,
        creator_id=current_user.id,
    )
    session.add(course)
    session.flush()
    session.refresh(course)
    log_activity(
        session,
        actor_id=current_user.id,
        action="create_course",
        entity_type="course",
        entity_id=course.id,
        details=f"Course '{course.title}' created",
    )
    session.commit()
    return course


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(course_id: int, session: Session = Depends(get_session)) -> CourseDetail:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    lessons = session.exec(select(Lesson).where(Lesson.course_id == course_id)).all()
    quiz_statement = (
        select(Quiz)
        .join(Lesson, Quiz.lesson_id == Lesson.id)
        .where(Lesson.course_id == course_id)
        .order_by(Quiz.created_at)
    )
    quizzes = session.exec(quiz_statement).all()
    return CourseDetail(
        **course.model_dump(),
        lessons=[LessonRead.model_validate(lesson, from_attributes=True) for lesson in lessons],
        quizzes=[_build_quiz_read(session, quiz) for quiz in quizzes],
    )


def _build_quiz_read(session: Session, quiz: Quiz) -> QuizRead:
    questions = session.exec(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)).all()
    return QuizRead(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        created_at=quiz.created_at,
        questions=[QuizQuestionRead.model_validate(q, from_attributes=True) for q in questions],
    )


@router.post(
    "/{course_id}/submit",
    response_model=CourseRead,
    dependencies=[Depends(require_roles(UserRole.CONTENT_CREATOR, UserRole.ADMIN))],
)
def submit_course(
    course_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only the course owner or admins can submit the course")
    course.status = CourseStatus.PENDING_REVIEW
    session.add(course)
    session.flush()
    log_activity(
        session,
        actor_id=current_user.id,
        action="submit_course",
        entity_type="course",
        entity_id=course.id,
        details="Course submitted for review",
    )
    session.commit()
    return course


@router.post(
    "/{course_id}/publish",
    response_model=CourseRead,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def publish_course(course_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user)) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.status = CourseStatus.PUBLISHED
    course.published_at = datetime.utcnow()
    session.add(course)
    session.flush()
    _create_notification(session, course.creator_id, f"Your course '{course.title}' is now published!")
    log_activity(
        session,
        actor_id=current_user.id,
        action="publish_course",
        entity_type="course",
        entity_id=course.id,
        details="Course published",
    )
    session.commit()
    return course


@router.post(
    "/{course_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.CONTENT_CREATOR, UserRole.ADMIN))],
)
def create_lesson(
    course_id: int,
    lesson_in: LessonCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Lesson:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only the course owner or admins can add lessons")
    lesson = Lesson(
        course_id=course_id,
        title=lesson_in.title,
        content=lesson_in.content,
        media_type=lesson_in.media_type,
        created_by_id=current_user.id,
    )
    session.add(lesson)
    session.flush()
    session.refresh(lesson)
    log_activity(
        session,
        actor_id=current_user.id,
        action="create_lesson",
        entity_type="lesson",
        entity_id=lesson.id,
        details=f"Lesson '{lesson.title}' created",
    )
    session.commit()
    return lesson


@router.post(
    "/lessons/{lesson_id}/submit",
    response_model=LessonRead,
    dependencies=[Depends(require_roles(UserRole.CONTENT_CREATOR, UserRole.ADMIN))],
)
def submit_lesson(
    lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only the lesson owner or admins can submit the lesson")
    lesson.status = LessonStatus.PENDING_REVIEW
    session.add(lesson)
    session.flush()
    log_activity(
        session,
        actor_id=current_user.id,
        action="submit_lesson",
        entity_type="lesson",
        entity_id=lesson.id,
        details="Lesson submitted for validation",
    )
    session.commit()
    return lesson


@router.post(
    "/lessons/{lesson_id}/approve",
    response_model=LessonRead,
    dependencies=[Depends(require_roles(UserRole.VALIDATOR, UserRole.ADMIN))],
)
def approve_lesson(
    lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson.status = LessonStatus.APPROVED
    lesson.approved_by_id = current_user.id
    session.add(lesson)
    session.flush()
    _create_notification(session, lesson.created_by_id, f"Lesson '{lesson.title}' approved")
    log_activity(
        session,
        actor_id=current_user.id,
        action="approve_lesson",
        entity_type="lesson",
        entity_id=lesson.id,
        details="Lesson approved by validator",
    )
    session.commit()
    return lesson


@router.get(
    "/lessons/pending",
    response_model=List[LessonRead],
    dependencies=[Depends(require_roles(UserRole.VALIDATOR, UserRole.ADMIN))],
)
def list_pending_lessons(session: Session = Depends(get_session)) -> List[Lesson]:
    statement = (
        select(Lesson)
        .where(Lesson.status == LessonStatus.PENDING_REVIEW)
        .order_by(Lesson.created_at.asc())
    )
    return session.exec(statement).all()


@router.post(
    "/lessons/{lesson_id}/quizzes",
    response_model=QuizRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.CONTENT_CREATOR, UserRole.ADMIN))],
)
def create_quiz(
    lesson_id: int,
    quiz_in: QuizCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Quiz:
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only the lesson owner or admins can manage quizzes")
    existing_quiz = session.exec(select(Quiz).where(Quiz.lesson_id == lesson_id)).first()
    if existing_quiz:
        raise HTTPException(status_code=400, detail="Quiz already exists for this lesson")
    quiz = Quiz(lesson_id=lesson_id, title=quiz_in.title)
    session.add(quiz)
    session.flush()
    for question_in in quiz_in.questions:
        question = QuizQuestion(
            quiz_id=quiz.id,
            prompt=question_in.prompt,
            options=question_in.options,
            answer_index=question_in.answer_index,
        )
        session.add(question)
    session.flush()
    log_activity(
        session,
        actor_id=current_user.id,
        action="create_quiz",
        entity_type="quiz",
        entity_id=quiz.id,
        details=f"Quiz '{quiz.title}' created",
    )
    session.commit()
    return _build_quiz_read(session, quiz)
