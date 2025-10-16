from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from . import auth
from .auth import require_roles
from .database import get_session, init_db, session_scope
from .models import (
    ActivityLog,
    Certificate,
    Chapter,
    Course,
    CourseStatus,
    CreditSource,
    CreditTransaction,
    Enrollment,
    Lesson,
    LessonStatus,
    LessonFeedback,
    Notification,
    Quiz,
    SponsorDonation,
    User,
    UserRole,
)

app = FastAPI(title="Udoy Learning Platform API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with session_scope() as session:
        ensure_seed_admin(session)

def ensure_seed_admin(session: Session) -> None:
    statement = select(User).where(User.role == UserRole.ADMIN)
    if not session.exec(statement).first():
        admin = User(
            email="admin@udoy.local",
            password_hash=auth.get_password_hash("admin123"),
            role=UserRole.ADMIN,
            full_name="Platform Admin",
            bio="Seed administrator account"
        )
        session.add(admin)
        session.commit()


def record_activity(session: Session, user_id: int, action: str, entity: str, reference_id: Optional[int] = None) -> None:
    session.add(ActivityLog(user_id=user_id, action=action, entity=entity, reference_id=reference_id))


def notify_user(session: Session, user_id: int, message: str) -> None:
    session.add(Notification(user_id=user_id, message=message))


def serialize_user(user: User) -> UserRead:
    return UserRead.from_orm(user)


def update_badges(user: User, enrollment: Enrollment) -> None:
    milestones = [25, 50, 75, 100]
    for milestone in milestones:
        if enrollment.progress_percent >= milestone and f"Progress {milestone}%" not in user.badges:
            user.badges.append(f"Progress {milestone}%")
    if enrollment.completed and "Course Champion" not in user.badges:
        user.badges.append("Course Champion")


def recalculate_progress(session: Session, enrollment: Enrollment) -> None:
    lessons_statement = select(Lesson.id).where(Lesson.course_id == enrollment.course_id, Lesson.status == LessonStatus.APPROVED)
    approved_lessons = [row[0] for row in session.exec(lessons_statement)]
    if not approved_lessons:
        enrollment.progress_percent = 0.0
        return
    completed_count = len(set(enrollment.completed_lessons) & set(approved_lessons))
    enrollment.progress_percent = round(100 * completed_count / len(approved_lessons), 2)
    if enrollment.progress_percent >= 100 and not enrollment.completed:
        enrollment.completed = True
        enrollment.completed_at = dt.datetime.utcnow()


def withdraw_from_sponsor_pool(session: Session, amount: int) -> int:
    remaining = amount
    donations = session.exec(select(SponsorDonation).where(SponsorDonation.remaining > 0).order_by(SponsorDonation.created_at)).all()
    for donation in donations:
        if remaining <= 0:
            break
        consume = min(donation.remaining, remaining)
        donation.remaining -= consume
        remaining -= consume
    return amount - remaining


def award_credits(session: Session, user: User, amount: int, source: CreditSource, note: Optional[str] = None) -> int:
    if amount <= 0:
        return 0
    consumed = amount
    if source in {CreditSource.COMPLETION, CreditSource.COACH}:
        consumed = withdraw_from_sponsor_pool(session, amount)
    if consumed <= 0:
        return 0
    user.credits += consumed
    session.add(CreditTransaction(user_id=user.id, amount=consumed, source=source, note=note))
    return consumed


def ensure_lesson_quiz(session: Session, lesson_id: int) -> None:
    statement = select(Quiz).where(Quiz.lesson_id == lesson_id)
    if not session.exec(statement).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lesson must have an associated quiz")


def build_course_summary(session: Session, course: Course) -> Dict[str, object]:
    lessons = session.exec(select(Lesson).where(Lesson.course_id == course.id)).all()
    enrollments = session.exec(select(Enrollment).where(Enrollment.course_id == course.id)).all()
    return {
        "course": course,
        "lesson_count": len(lessons),
        "enrollment_count": len(enrollments),
        "completion_rate": round(
            100 * sum(1 for e in enrollments if e.completed) / len(enrollments), 2
        ) if enrollments else 0.0,
    }


class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    role: UserRole = UserRole.STUDENT
    bio: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CourseCreateRequest(BaseModel):
    title: str
    description: str
    subject: str
    level: str


class LessonCreateRequest(BaseModel):
    title: str
    text_content: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    resources: List[str] = Field(default_factory=list)


class QuizCreateRequest(BaseModel):
    question: str
    options: List[str] = Field(min_items=2)
    correct_option: int
    explanation: Optional[str] = None


class QuizAttemptRequest(BaseModel):
    answer_index: int


class ChapterCreateRequest(BaseModel):
    title: str
    sequence: int


class CreditAllocationRequest(BaseModel):
    student_id: int
    amount: int = Field(gt=0)
    note: Optional[str] = None


class RecommendationResponse(BaseModel):
    recommended_courses: List[int]
    reasons: Dict[int, List[str]]


class NotificationResponse(BaseModel):
    id: int
    message: str
    created_at: dt.datetime
    read: bool


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_data: Optional[Dict[str, object]] = None


class RoleUpdateRequest(BaseModel):
    role: UserRole


class LessonApprovalRequest(BaseModel):
    decision: str = Field(regex="^(approve|reject)$")
    feedback: Optional[str] = None


class DonationRequest(BaseModel):
    amount: int = Field(gt=0)


class CourseStatusUpdate(BaseModel):
    status: CourseStatus


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    full_name: str
    bio: Optional[str]
    credits: int
    badges: List[str]
    profile_data: Dict[str, object]
    created_at: dt.datetime

    class Config:
        orm_mode = True


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


@app.post("/auth/register", response_model=UserRead)
def register_user(payload: RegistrationRequest, session: Session = Depends(get_session)) -> UserRead:
    if session.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=payload.email,
        password_hash=auth.get_password_hash(payload.password),
        role=payload.role,
        full_name=payload.full_name,
        bio=payload.bio
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    notify_user(session, user.id, "Welcome to Udoy! Explore your dashboard to get started.")
    record_activity(session, user.id, "registered", "user", user.id)
    return serialize_user(user)


@app.post("/auth/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> Dict[str, object]:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = auth.create_session_token(user.id, session)
    record_activity(session, user.id, "login", "user")
    return {"token": token, "user": serialize_user(user)}


@app.get("/users/me", response_model=UserRead)
def me(current: User = Depends(auth.get_current_user)) -> UserRead:
    return serialize_user(current)


@app.put("/users/me", response_model=UserRead)
def update_profile(update: ProfileUpdateRequest, current: User = Depends(auth.get_current_user), session: Session = Depends(get_session)) -> UserRead:
    data = update.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(current, key, value)
    session.add(current)
    record_activity(session, current.id, "profile_updated", "user", current.id)
    return serialize_user(current)


@app.get("/users", response_model=List[UserRead])
def list_users(_: User = Depends(require_roles(UserRole.ADMIN)), session: Session = Depends(get_session)) -> List[UserRead]:
    return [serialize_user(user) for user in session.exec(select(User)).all()]


@app.post("/users/{user_id}/role", response_model=UserRead)
def change_role(user_id: int, payload: RoleUpdateRequest, _: User = Depends(require_roles(UserRole.ADMIN)), session: Session = Depends(get_session)) -> UserRead:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = payload.role
    session.add(user)
    record_activity(session, user_id, "role_changed", "user", user_id)
    notify_user(session, user_id, f"Your role has been updated to {payload.role.value}.")
    return serialize_user(user)


@app.post("/courses", response_model=Course)
def create_course(payload: CourseCreateRequest, current: User = Depends(require_roles(UserRole.CREATOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Course:
    course = Course(
        title=payload.title,
        description=payload.description,
        subject=payload.subject,
        level=payload.level,
        creator_id=current.id,
        status=CourseStatus.DRAFT
    )
    session.add(course)
    session.flush()
    record_activity(session, current.id, "course_created", "course", course.id)
    notify_user(session, current.id, f"Course '{course.title}' created. Add lessons to continue.")
    return course


@app.get("/courses", response_model=List[Course])
def list_courses(session: Session = Depends(get_session)) -> List[Course]:
    return session.exec(select(Course)).all()


@app.post("/courses/{course_id}/status", response_model=Course)
def update_course_status(course_id: int, payload: CourseStatusUpdate, current: User = Depends(require_roles(UserRole.ADMIN, UserRole.COACH)), session: Session = Depends(get_session)) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if payload.status == CourseStatus.PUBLISHED:
        lessons = session.exec(select(Lesson).where(Lesson.course_id == course_id, Lesson.status == LessonStatus.APPROVED)).all()
        if not lessons:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot publish without approved lessons")
        for lesson in lessons:
            ensure_lesson_quiz(session, lesson.id)
    course.status = payload.status
    session.add(course)
    record_activity(session, current.id, "course_status_updated", "course", course.id)
    notify_user(session, course.creator_id, f"Course '{course.title}' status updated to {payload.status.value}.")
    return course


@app.get("/creator/courses/{course_id}/insights")
def course_insights(course_id: int, current: User = Depends(require_roles(UserRole.CREATOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Dict[str, object]:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if current.role != UserRole.ADMIN and course.creator_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    enrollments = session.exec(select(Enrollment).where(Enrollment.course_id == course_id)).all()
    lessons = session.exec(select(Lesson).where(Lesson.course_id == course_id)).all()
    lesson_ids = [lesson.id for lesson in lessons]
    feedback_rows = []
    if lesson_ids:
        feedback_rows = session.exec(select(LessonFeedback).where(LessonFeedback.lesson_id.in_(lesson_ids))).all()
    average_rating = round(sum(f.rating for f in feedback_rows) / len(feedback_rows), 2) if feedback_rows else None
    top_students = sorted(enrollments, key=lambda e: e.progress_percent, reverse=True)[:5]
    top_students_data = [
        {
            "student": serialize_user(session.get(User, enrollment.user_id)),
            "progress": enrollment.progress_percent,
            "completed": enrollment.completed,
        }
        for enrollment in top_students
    ]
    return {
        "course": course,
        "enrollments": len(enrollments),
        "completions": sum(1 for e in enrollments if e.completed),
        "average_rating": average_rating,
        "top_students": top_students_data,
    }


@app.post("/courses/{course_id}/lessons", response_model=Lesson)
def create_lesson(course_id: int, payload: LessonCreateRequest, current: User = Depends(require_roles(UserRole.CREATOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Lesson:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if course.creator_id != current.id and current.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the course creator or admin can add lessons")
    lesson = Lesson(
        course_id=course_id,
        title=payload.title,
        text_content=payload.text_content,
        video_url=payload.video_url,
        audio_url=payload.audio_url,
        creator_id=current.id,
        resources=payload.resources,
        status=LessonStatus.REVIEW if current.role == UserRole.ADMIN else LessonStatus.DRAFT
    )
    session.add(lesson)
    session.flush()
    record_activity(session, current.id, "lesson_created", "lesson", lesson.id)
    notify_user(session, course.creator_id, f"Lesson '{lesson.title}' added to course '{course.title}'.")
    return lesson


@app.post("/lessons/{lesson_id}/submit", response_model=Lesson)
def submit_lesson_for_review(lesson_id: int, current: User = Depends(require_roles(UserRole.CREATOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    if lesson.creator_id != current.id and current.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot submit this lesson")
    ensure_lesson_quiz(session, lesson_id)
    lesson.status = LessonStatus.REVIEW
    session.add(lesson)
    validators = session.exec(select(User).where(User.role == UserRole.VALIDATOR)).all()
    for validator in validators:
        notify_user(session, validator.id, f"Lesson '{lesson.title}' is awaiting review.")
    record_activity(session, current.id, "lesson_submitted", "lesson", lesson.id)
    return lesson


@app.post("/lessons/{lesson_id}/approve", response_model=Lesson)
def approve_lesson(lesson_id: int, payload: LessonApprovalRequest, current: User = Depends(require_roles(UserRole.VALIDATOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    if payload.decision == "approve":
        lesson.status = LessonStatus.APPROVED
        lesson.validator_id = current.id
        notify_user(session, lesson.creator_id, f"Lesson '{lesson.title}' approved.")
    else:
        lesson.status = LessonStatus.DRAFT
        notify_user(session, lesson.creator_id, f"Lesson '{lesson.title}' requires updates: {payload.feedback or 'see comments'}")
    record_activity(session, current.id, f"lesson_{payload.decision}", "lesson", lesson.id)
    session.add(lesson)
    return lesson


@app.post("/lessons/{lesson_id}/quiz", response_model=Quiz)
def create_quiz(lesson_id: int, payload: QuizCreateRequest, current: User = Depends(require_roles(UserRole.CREATOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Quiz:
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    if lesson.creator_id != current.id and current.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify this lesson")
    if not (0 <= payload.correct_option < len(payload.options)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Correct option index out of range")
    quiz = Quiz(lesson_id=lesson_id, question=payload.question, options=payload.options, correct_option=payload.correct_option, explanation=payload.explanation)
    session.add(quiz)
    session.flush()
    record_activity(session, current.id, "quiz_created", "quiz", quiz.id)
    return quiz


@app.post("/courses/{course_id}/chapters", response_model=Chapter)
def create_chapter(course_id: int, payload: ChapterCreateRequest, current: User = Depends(require_roles(UserRole.COACH, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Chapter:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    chapter = Chapter(course_id=course_id, title=payload.title, sequence=payload.sequence)
    session.add(chapter)
    session.flush()
    record_activity(session, current.id, "chapter_created", "chapter", chapter.id)
    notify_user(session, course.creator_id, f"Coach added chapter '{chapter.title}' to course '{course.title}'.")
    return chapter


@app.post("/chapters/{chapter_id}/assign/{lesson_id}", response_model=Lesson)
def assign_lesson_to_chapter(chapter_id: int, lesson_id: int, current: User = Depends(require_roles(UserRole.COACH, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Lesson:
    chapter = session.get(Chapter, chapter_id)
    lesson = session.get(Lesson, lesson_id)
    if not chapter or not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter or lesson not found")
    if chapter.course_id != lesson.course_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lesson must belong to the same course")
    lesson.chapter_id = chapter_id
    session.add(lesson)
    record_activity(session, current.id, "lesson_assigned", "lesson", lesson.id)
    notify_user(session, lesson.creator_id, f"Lesson '{lesson.title}' assigned to chapter '{chapter.title}'.")
    return lesson


@app.post("/courses/{course_id}/enroll", response_model=Enrollment)
def enroll(course_id: int, current: User = Depends(require_roles(UserRole.STUDENT)), session: Session = Depends(get_session)) -> Enrollment:
    if session.exec(select(Enrollment).where(Enrollment.user_id == current.id, Enrollment.course_id == course_id)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already enrolled")
    course = session.get(Course, course_id)
    if not course or course.status != CourseStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course not available for enrollment")
    enrollment = Enrollment(user_id=current.id, course_id=course_id)
    session.add(enrollment)
    record_activity(session, current.id, "enrolled", "course", course_id)
    notify_user(session, course.creator_id, f"{current.full_name} enrolled in '{course.title}'.")
    return enrollment


@app.post("/quizzes/{quiz_id}/attempt")
def attempt_quiz(quiz_id: int, payload: QuizAttemptRequest, current: User = Depends(require_roles(UserRole.STUDENT)), session: Session = Depends(get_session)) -> Dict[str, object]:
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    lesson = session.get(Lesson, quiz.lesson_id)
    if not lesson or lesson.status != LessonStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lesson not available")
    enrollment = session.exec(select(Enrollment).where(Enrollment.user_id == current.id, Enrollment.course_id == lesson.course_id)).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must enroll before attempting quizzes")
    if not (0 <= payload.answer_index < len(quiz.options)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Answer index out of range")
    correct = payload.answer_index == quiz.correct_option
    enrollment.quiz_scores[str(quiz.id)] = {"correct": correct, "submitted": dt.datetime.utcnow().isoformat()}
    if correct and lesson.id not in enrollment.completed_lessons:
        enrollment.completed_lessons.append(lesson.id)
    enrollment.resume_lesson_id = lesson.id
    recalculate_progress(session, enrollment)
    update_badges(current, enrollment)
    session.add(enrollment)
    session.add(current)
    record_activity(session, current.id, "quiz_attempt", "quiz", quiz.id)
    if correct:
        notify_user(session, current.id, f"Great job! You answered '{lesson.title}' quiz correctly.")
    else:
        notify_user(session, current.id, f"Keep trying! Review '{lesson.title}' and attempt again.")
    response = {"correct": correct, "explanation": quiz.explanation, "progress": enrollment.progress_percent}
    if enrollment.completed and not session.exec(select(Certificate).where(Certificate.user_id == current.id, Certificate.course_id == lesson.course_id)).first():
        certificate = Certificate(user_id=current.id, course_id=lesson.course_id)
        session.add(certificate)
        awarded = award_credits(session, current, amount=50, source=CreditSource.COMPLETION, note=f"Course {lesson.course_id} completion")
        notify_user(session, current.id, f"Course completed! You earned {awarded} credits and a certificate.")
        response["certificate_issued"] = True
        response["credits_awarded"] = awarded
    return response


@app.post("/lessons/{lesson_id}/feedback", response_model=Dict[str, object])
def leave_feedback(lesson_id: int, payload: FeedbackRequest, current: User = Depends(require_roles(UserRole.STUDENT)), session: Session = Depends(get_session)) -> Dict[str, object]:
    lesson = session.get(Lesson, lesson_id)
    if not lesson or lesson.status != LessonStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not available")
    enrollment = session.exec(select(Enrollment).where(Enrollment.user_id == current.id, Enrollment.course_id == lesson.course_id)).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enroll in the course to leave feedback")
    feedback = LessonFeedback(lesson_id=lesson_id, user_id=current.id, rating=payload.rating, comment=payload.comment)
    session.add(feedback)
    notify_user(session, lesson.creator_id, f"{current.full_name} rated lesson '{lesson.title}' {payload.rating} stars.")
    record_activity(session, current.id, "lesson_feedback", "lesson", lesson_id)
    return {"status": "received"}


@app.get("/lessons/{lesson_id}/feedback")
def get_feedback(lesson_id: int, current: User = Depends(require_roles(UserRole.CREATOR, UserRole.VALIDATOR, UserRole.COACH, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Dict[str, object]:
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    feedback_rows = session.exec(select(LessonFeedback).where(LessonFeedback.lesson_id == lesson_id)).all()
    avg_rating = round(sum(f.rating for f in feedback_rows) / len(feedback_rows), 2) if feedback_rows else None
    entries = [
        {
            "student": serialize_user(session.get(User, fb.user_id)),
            "rating": fb.rating,
            "comment": fb.comment,
            "created_at": fb.created_at,
        }
        for fb in feedback_rows
    ]
    return {"lesson": lesson, "average_rating": avg_rating, "feedback": entries}


@app.post("/coaches/credits")
def coach_allocate_credits(payload: CreditAllocationRequest, current: User = Depends(require_roles(UserRole.COACH, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Dict[str, object]:
    student = session.get(User, payload.student_id)
    if not student or student.role != UserRole.STUDENT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    awarded = award_credits(session, student, payload.amount, CreditSource.COACH, payload.note)
    if awarded <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No credits available in sponsor pool")
    notify_user(session, student.id, f"Coach {current.full_name} awarded you {awarded} credits. {payload.note or ''}")
    record_activity(session, current.id, "credit_awarded", "user", student.id)
    return {"student": serialize_user(student), "awarded": awarded}


@app.post("/sponsors/donate")
def sponsor_donate(payload: DonationRequest, current: User = Depends(require_roles(UserRole.SPONSOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Dict[str, object]:
    donation = SponsorDonation(sponsor_id=current.id, amount=payload.amount, remaining=payload.amount)
    session.add(donation)
    session.add(CreditTransaction(user_id=None, amount=payload.amount, source=CreditSource.SPONSOR, note="Sponsor donation"))
    notify_user(session, current.id, f"Thank you for donating {payload.amount} credits. They will inspire more learning!")
    record_activity(session, current.id, "donation", "credits", donation.id)
    return {"donation_id": donation.id, "remaining": donation.remaining}


@app.get("/students/{student_id}/dashboard")
def student_dashboard(student_id: int, current: User = Depends(auth.get_current_user), session: Session = Depends(get_session)) -> Dict[str, object]:
    if current.role != UserRole.ADMIN and current.id != student_id and current.role != UserRole.COACH:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    student = session.get(User, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    enrollments = session.exec(select(Enrollment).where(Enrollment.user_id == student_id)).all()
    progress = [
        {
            "course": session.get(Course, enrollment.course_id),
            "progress": enrollment.progress_percent,
            "completed": enrollment.completed,
            "resume_lesson_id": enrollment.resume_lesson_id,
        }
        for enrollment in enrollments
    ]
    notifications = session.exec(select(Notification).where(Notification.user_id == student_id).order_by(Notification.created_at.desc()).limit(10)).all()
    return {
        "student": serialize_user(student),
        "progress": progress,
        "badges": student.badges,
        "notifications": notifications,
    }


@app.get("/recommendations", response_model=RecommendationResponse)
def recommendations(current: User = Depends(require_roles(UserRole.STUDENT)), session: Session = Depends(get_session)) -> RecommendationResponse:
    enrollments = session.exec(select(Enrollment).where(Enrollment.user_id == current.id)).all()
    completed_courses = [enrollment.course_id for enrollment in enrollments if enrollment.completed]
    subjects_counter: Counter[str] = Counter()
    for course_id in completed_courses:
        course = session.get(Course, course_id)
        if course:
            subjects_counter[course.subject] += 1
    candidate_courses = session.exec(select(Course).where(Course.status == CourseStatus.PUBLISHED)).all()
    recommended: List[int] = []
    reasons: Dict[int, List[str]] = defaultdict(list)
    for course in candidate_courses:
        if course.id in completed_courses:
            continue
        if subjects_counter.get(course.subject):
            recommended.append(course.id)
            reasons[course.id].append("Continue mastering subject")
        if course.level == "beginner" and not completed_courses:
            recommended.append(course.id)
            reasons[course.id].append("Start with beginner-friendly content")
    if not recommended and candidate_courses:
        recommended.append(candidate_courses[0].id)
        reasons[candidate_courses[0].id].append("Popular course suggestion")
    return RecommendationResponse(recommended_courses=recommended, reasons=reasons)


@app.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(current: User = Depends(auth.get_current_user), session: Session = Depends(get_session)) -> List[NotificationResponse]:
    rows = session.exec(select(Notification).where(Notification.user_id == current.id).order_by(Notification.created_at.desc())).all()
    return [
        NotificationResponse(id=row.id, message=row.message, created_at=row.created_at, read=row.read) for row in rows
    ]


@app.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, current: User = Depends(auth.get_current_user), session: Session = Depends(get_session)) -> Dict[str, object]:
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.read = True
    session.add(notification)
    return {"status": "ok"}


@app.get("/admin/analytics")
def admin_analytics(_: User = Depends(require_roles(UserRole.ADMIN)), session: Session = Depends(get_session)) -> Dict[str, object]:
    user_counts = Counter(user.role for user in session.exec(select(User)).all())
    courses = session.exec(select(Course)).all()
    sponsor_pool = sum(d.remaining for d in session.exec(select(SponsorDonation)).all())
    leaderboard_users = session.exec(select(User).where(User.role == UserRole.STUDENT).order_by(User.credits.desc()).limit(5)).all()
    leaderboard = [serialize_user(user) for user in leaderboard_users]
    course_summaries = [build_course_summary(session, course) for course in courses]
    return {
        "users": user_counts,
        "courses": course_summaries,
        "sponsor_pool": sponsor_pool,
        "leaderboard": leaderboard,
        "activity_logs": session.exec(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(20)).all(),
    }


@app.get("/coach/students")
def coach_students(current: User = Depends(require_roles(UserRole.COACH, UserRole.ADMIN)), session: Session = Depends(get_session)) -> List[Dict[str, object]]:
    enrollments = session.exec(select(Enrollment)).all()
    student_map: Dict[int, Dict[str, object]] = {}
    for enrollment in enrollments:
        student = session.get(User, enrollment.user_id)
        if not student or student.role != UserRole.STUDENT:
            continue
        entry = student_map.setdefault(student.id, {"student": serialize_user(student), "courses": []})
        entry["courses"].append({
            "course": session.get(Course, enrollment.course_id),
            "progress": enrollment.progress_percent,
            "completed": enrollment.completed,
        })
    return list(student_map.values())


@app.get("/sponsor/reports")
def sponsor_reports(current: User = Depends(require_roles(UserRole.SPONSOR, UserRole.ADMIN)), session: Session = Depends(get_session)) -> Dict[str, object]:
    donations = session.exec(select(SponsorDonation).where(SponsorDonation.sponsor_id == current.id)).all()
    transactions = session.exec(select(CreditTransaction).where(CreditTransaction.source != CreditSource.SPONSOR, CreditTransaction.user_id.isnot(None))).all()
    impact = defaultdict(int)
    for txn in transactions:
        if txn.source in {CreditSource.COMPLETION, CreditSource.COACH}:
            impact[txn.source.value] += txn.amount
    return {
        "donations": donations,
        "impact": impact,
    }
