from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ...db import get_session
from ...models import (
    Course,
    CourseStatus,
    CreditSource,
    CreditTransaction,
    Enrollment,
    EnrollmentStatus,
    Notification,
    User,
    UserRole,
)
from ...schemas import EnrollmentProgressUpdate, EnrollmentRead
from ..deps import get_current_active_user, log_activity, require_roles

router = APIRouter(prefix="/courses", tags=["enrollments"])


@router.post(
    "/{course_id}/enroll",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def enroll_in_course(
    course_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
) -> Enrollment:
    course = session.get(Course, course_id)
    if not course or course.status != CourseStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Course not available for enrollment")
    existing = session.exec(
        select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.student_id == current_user.id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
    enrollment = Enrollment(student_id=current_user.id, course_id=course_id)
    session.add(enrollment)
    session.flush()
    session.refresh(enrollment)
    if course.creator_id:
        notification = Notification(
            user_id=course.creator_id,
            message=f"{current_user.full_name} enrolled in '{course.title}'",
        )
        session.add(notification)
    log_activity(
        session,
        actor_id=current_user.id,
        action="enroll_course",
        entity_type="enrollment",
        entity_id=enrollment.id,
        details=f"Enrolled in course {course.title}",
    )
    session.commit()
    return enrollment


@router.get("/me/enrollments", response_model=List[EnrollmentRead])
def list_my_enrollments(
    session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user)
) -> List[Enrollment]:
    statement = select(Enrollment).where(Enrollment.student_id == current_user.id)
    return session.exec(statement).all()


@router.post(
    "/{course_id}/progress",
    response_model=EnrollmentRead,
)
def update_progress(
    course_id: int,
    progress_update: EnrollmentProgressUpdate,
    student_id: int | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Enrollment:
    if current_user.role == UserRole.STUDENT:
        target_student_id = current_user.id
    elif current_user.role in {UserRole.COACH, UserRole.ADMIN}:
        if student_id is None:
            raise HTTPException(status_code=400, detail="student_id is required for coaches and admins")
        target_student_id = student_id
    else:
        raise HTTPException(status_code=403, detail="Not allowed to update progress")
    enrollment = session.exec(
        select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.student_id == target_student_id)
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if progress_update.progress < 0 or progress_update.progress > 1:
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 1")
    enrollment.progress = progress_update.progress
    enrollment.last_lesson_id = progress_update.last_lesson_id
    enrollment.updated_at = datetime.utcnow()
    course = session.get(Course, course_id)
    awarded_credit = False
    if progress_update.mark_complete:
        enrollment.status = EnrollmentStatus.COMPLETED
        if enrollment.credits_awarded == 0:
            credit = CreditTransaction(
                user_id=enrollment.student_id,
                amount=100,
                source=CreditSource.SYSTEM,
                description=f"Course completion reward for '{course.title if course else enrollment.course_id}'",
            )
            session.add(credit)
            enrollment.credits_awarded = credit.amount
            awarded_credit = True
            notification = Notification(
                user_id=enrollment.student_id,
                message=(
                    f"Congratulations! You've earned 100 credits for completing '{course.title}'."
                    if course
                    else "Congratulations on your course completion!"
                ),
            )
            session.add(notification)
    session.add(enrollment)
    session.flush()
    details = "Progress updated"
    if awarded_credit:
        details += " and completion credits awarded"
    log_activity(
        session,
        actor_id=current_user.id,
        action="update_progress",
        entity_type="enrollment",
        entity_id=enrollment.id,
        details=details,
    )
    session.commit()
    return enrollment
