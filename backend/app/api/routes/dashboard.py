from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, or_, select

from ...db import get_session
from ...models import ActivityLog, Course, CourseStatus, Enrollment, Lesson, LessonStatus, User, UserRole
from ...schemas import (
    ActivityLogRead,
    CourseRead,
    DashboardCourse,
    DashboardOverview,
    EnrollmentStatus,
    LessonRead,
)
from ..deps import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _build_course_summary(session: Session, enrollment) -> DashboardCourse | None:
    course = session.get(Course, enrollment.course_id)
    if not course:
        return None
    return DashboardCourse(
        course=CourseRead.model_validate(course, from_attributes=True),
        progress=enrollment.progress,
        status=enrollment.status,
        credits_awarded=enrollment.credits_awarded,
    )


@router.get("", response_model=DashboardOverview)
def get_dashboard(session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user)) -> DashboardOverview:
    active_courses: List[DashboardCourse] = []
    pending_lessons: List[LessonRead] = []

    if current_user.role == UserRole.STUDENT:
        enrollments = session.exec(select(Enrollment).where(Enrollment.student_id == current_user.id)).all()
        active_courses = [summary for enrollment in enrollments if (summary := _build_course_summary(session, enrollment))]
    elif current_user.role == UserRole.CONTENT_CREATOR:
        courses = session.exec(select(Course).where(Course.creator_id == current_user.id)).all()
        active_courses = [
            DashboardCourse(
                course=CourseRead.model_validate(course, from_attributes=True),
                progress=1.0 if course.status == CourseStatus.PUBLISHED else 0.0,
                status=EnrollmentStatus.IN_PROGRESS,
                credits_awarded=0,
            )
            for course in courses
        ]
        pending_lessons = session.exec(
            select(Lesson).where(Lesson.created_by_id == current_user.id, Lesson.status == LessonStatus.PENDING_REVIEW)
        ).all()
    elif current_user.role == UserRole.VALIDATOR:
        pending_lessons = session.exec(select(Lesson).where(Lesson.status == LessonStatus.PENDING_REVIEW)).all()
    else:
        courses = session.exec(select(Course).order_by(Course.created_at.desc()).limit(5)).all()
        active_courses = [
            DashboardCourse(
                course=CourseRead.model_validate(course, from_attributes=True),
                progress=0.0,
                status=EnrollmentStatus.IN_PROGRESS,
                credits_awarded=0,
            )
            for course in courses
        ]

    pending_lessons = [LessonRead.model_validate(lesson, from_attributes=True) for lesson in pending_lessons]

    activity_query = (
        select(ActivityLog)
        .where(or_(ActivityLog.actor_id == current_user.id, ActivityLog.actor_id.is_(None)))
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
    )
    recent_activity = [
        ActivityLogRead.model_validate(activity, from_attributes=True)
        for activity in session.exec(activity_query).all()
    ]

    return DashboardOverview(active_courses=active_courses, pending_lessons=pending_lessons, recent_activity=recent_activity)
