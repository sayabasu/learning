from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, JSON, String
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    STUDENT = "student"
    CREATOR = "creator"
    VALIDATOR = "validator"
    COACH = "coach"
    ADMIN = "admin"
    SPONSOR = "sponsor"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String, unique=True, index=True))
    password_hash: str
    role: UserRole = Field(default=UserRole.STUDENT)
    full_name: str
    bio: Optional[str] = None
    credits: int = 0
    badges: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    profile_data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class SessionToken(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class CourseStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "in_review"
    PUBLISHED = "published"


class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    subject: str
    level: str
    creator_id: int = Field(foreign_key="user.id")
    status: CourseStatus = Field(default=CourseStatus.DRAFT)
    recommended_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class Chapter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    title: str
    sequence: int = Field(default=1)


class LessonStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "in_review"
    APPROVED = "approved"


class Lesson(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    chapter_id: Optional[int] = Field(default=None, foreign_key="chapter.id")
    title: str
    text_content: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    creator_id: int = Field(foreign_key="user.id")
    validator_id: Optional[int] = Field(default=None, foreign_key="user.id")
    status: LessonStatus = Field(default=LessonStatus.DRAFT)
    resources: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class Quiz(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key="lesson.id")
    question: str
    options: List[str] = Field(sa_column=Column(JSON))
    correct_option: int
    explanation: Optional[str] = None


class Enrollment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    course_id: int = Field(foreign_key="course.id")
    progress_percent: float = 0.0
    completed: bool = False
    resume_lesson_id: Optional[int] = Field(default=None, foreign_key="lesson.id")
    quiz_scores: dict = Field(default_factory=dict, sa_column=Column(JSON))
    completed_lessons: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    started_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    completed_at: Optional[dt.datetime] = None


class Certificate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    course_id: int = Field(foreign_key="course.id")
    issued_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class CreditSource(str, Enum):
    SPONSOR = "sponsor"
    COMPLETION = "completion"
    COACH = "coach"


class CreditTransaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    amount: int
    source: CreditSource
    note: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class SponsorDonation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sponsor_id: int = Field(foreign_key="user.id")
    amount: int
    remaining: int
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    message: str
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    read: bool = False


class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    action: str
    entity: str
    reference_id: Optional[int] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class LessonFeedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key="lesson.id")
    user_id: int = Field(foreign_key="user.id")
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
