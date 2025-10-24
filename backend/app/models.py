from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    ADMIN = "admin"
    STUDENT = "student"
    CONTENT_CREATOR = "content_creator"
    VALIDATOR = "validator"
    COACH = "coach"
    SPONSOR = "sponsor"


class CourseStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"


class LessonStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"


class EnrollmentStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CreditSource(str, Enum):
    SPONSOR = "sponsor"
    COACH = "coach"
    SYSTEM = "system"


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    full_name: str
    role: UserRole = Field(default=UserRole.STUDENT)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    courses: list["Course"] = Relationship(back_populates="creator")
    enrollments: list["Enrollment"] = Relationship(back_populates="student")
    notifications: list["Notification"] = Relationship(back_populates="user")


class Course(SQLModel, table=True):
    __tablename__ = "courses"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    subject: str
    status: CourseStatus = Field(default=CourseStatus.DRAFT)
    creator_id: int = Field(foreign_key="users.id")
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    creator: Optional[User] = Relationship(back_populates="courses")
    lessons: list["Lesson"] = Relationship(back_populates="course")


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id")
    title: str
    content: str
    media_type: str
    status: LessonStatus = Field(default=LessonStatus.DRAFT)
    created_by_id: int = Field(foreign_key="users.id")
    approved_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    course: Optional[Course] = Relationship(back_populates="lessons")
    quiz: Optional["Quiz"] = Relationship(back_populates="lesson")


class Quiz(SQLModel, table=True):
    __tablename__ = "quizzes"

    id: Optional[int] = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key="lessons.id", unique=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    lesson: Optional[Lesson] = Relationship(back_populates="quiz")
    questions: list["QuizQuestion"] = Relationship(back_populates="quiz")


class QuizQuestion(SQLModel, table=True):
    __tablename__ = "quiz_questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    quiz_id: int = Field(foreign_key="quizzes.id")
    prompt: str
    options: list[str] = Field(sa_column=Column(JSON))
    answer_index: int

    quiz: Optional[Quiz] = Relationship(back_populates="questions")


class QuizAttempt(SQLModel, table=True):
    __tablename__ = "quiz_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)
    quiz_id: int = Field(foreign_key="quizzes.id")
    student_id: int = Field(foreign_key="users.id")
    score: float
    responses: list[int] = Field(sa_column=Column(JSON))
    attempted_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    course_id: int = Field(foreign_key="courses.id")
    progress: float = Field(default=0.0)
    status: EnrollmentStatus = Field(default=EnrollmentStatus.IN_PROGRESS)
    credits_awarded: int = Field(default=0)
    last_lesson_id: Optional[int] = Field(default=None, foreign_key="lessons.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    student: Optional[User] = Relationship(back_populates="enrollments")


class CreditTransaction(SQLModel, table=True):
    __tablename__ = "credit_transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    amount: int
    source: CreditSource
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    message: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional[User] = Relationship(back_populates="notifications")


class ActivityLog(SQLModel, table=True):
    __tablename__ = "activity_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_id: Optional[int] = Field(default=None, foreign_key="users.id")
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
