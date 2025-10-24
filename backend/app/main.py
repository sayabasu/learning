from __future__ import annotations

from fastapi import FastAPI

from .api.routes import auth, courses, credits, dashboard, enrollments, notifications, quizzes, users
from .core.config import get_settings
from .core.security import get_password_hash
from .db import engine, init_db
from .models import User, UserRole
from .api.deps import get_user_by_email
from sqlmodel import Session

settings = get_settings()

app = FastAPI(title="Udoy Learning Platform API", version="1.0.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with Session(engine) as session:
        admin = get_user_by_email(session, settings.initial_admin_email)
        if not admin:
            admin_user = User(
                email=settings.initial_admin_email,
                full_name="Udoy Administrator",
                role=UserRole.ADMIN,
                hashed_password=get_password_hash(settings.initial_admin_password),
            )
            session.add(admin_user)
            session.commit()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(enrollments.router)
app.include_router(quizzes.router)
app.include_router(credits.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    return {"message": "Udoy learning platform API is running"}
