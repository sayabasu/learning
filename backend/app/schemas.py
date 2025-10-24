from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, EmailStr, Field as PydanticField
from sqlmodel import SQLModel

from .models import (
    CourseStatus,
    CreditSource,
    EnrollmentStatus,
    LessonStatus,
    UserRole,
)


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None
    model_config = ConfigDict(extra="ignore")


class UserBase(SQLModel):
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class UserRead(UserBase):
    id: int
    created_at: datetime


class UserCreate(SQLModel):
    email: EmailStr
    full_name: str
    password: str


class UserCreateWithRole(UserCreate):
    role: UserRole


class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class CourseBase(SQLModel):
    title: str
    description: str
    subject: str
    status: CourseStatus


class CourseCreate(SQLModel):
    title: str
    description: str
    subject: str


class CourseRead(CourseBase):
    id: int
    creator_id: int
    published_at: Optional[datetime] = None
    created_at: datetime


class LessonBase(SQLModel):
    title: str
    content: str
    media_type: str
    status: LessonStatus


class LessonCreate(SQLModel):
    title: str
    content: str
    media_type: str


class LessonRead(LessonBase):
    id: int
    course_id: int
    created_by_id: int
    approved_by_id: Optional[int] = None
    created_at: datetime


class QuizQuestionCreate(SQLModel):
    prompt: str
    options: List[str]
    answer_index: int = PydanticField(ge=0)


class QuizCreate(SQLModel):
    title: str
    questions: List[QuizQuestionCreate]


class QuizQuestionRead(SQLModel):
    id: int
    prompt: str
    options: List[str]
    answer_index: int


class QuizRead(SQLModel):
    id: int
    lesson_id: int
    title: str
    created_at: datetime
    questions: List[QuizQuestionRead]


class QuizAttemptCreate(SQLModel):
    responses: List[int]


class QuizAttemptRead(SQLModel):
    id: int
    quiz_id: int
    student_id: int
    score: float
    responses: List[int]
    attempted_at: datetime


class EnrollmentBase(SQLModel):
    progress: float
    status: EnrollmentStatus
    credits_awarded: int
    last_lesson_id: Optional[int]


class EnrollmentCreate(SQLModel):
    course_id: int


class EnrollmentRead(EnrollmentBase):
    id: int
    student_id: int
    course_id: int
    created_at: datetime
    updated_at: datetime


class EnrollmentProgressUpdate(SQLModel):
    progress: float
    last_lesson_id: Optional[int] = None
    mark_complete: bool = False


class CreditTransactionCreate(SQLModel):
    user_id: int
    amount: int
    source: CreditSource
    description: str


class CreditTransactionRead(SQLModel):
    id: int
    user_id: int
    amount: int
    source: CreditSource
    description: str
    created_at: datetime


class CreditAwardRequest(SQLModel):
    student_id: int
    amount: int
    description: str


class CreditDonationRequest(SQLModel):
    amount: int
    description: str


class NotificationRead(SQLModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime


class NotificationUpdate(SQLModel):
    is_read: bool


class ActivityLogRead(SQLModel):
    id: int
    actor_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[int]
    details: Optional[str]
    created_at: datetime


class DashboardCourse(SQLModel):
    course: CourseRead
    progress: float
    status: EnrollmentStatus
    credits_awarded: int


class DashboardOverview(SQLModel):
    active_courses: List[DashboardCourse]
    pending_lessons: List[LessonRead]
    recent_activity: List[ActivityLogRead]


class CourseDetail(CourseRead):
    lessons: List[LessonRead]
    quizzes: List[QuizRead]
