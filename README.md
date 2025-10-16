# Learning

This document outlines the structure and functionality of the **Udoy learning platform** in clear, simple terms. It explains what the website will be, how it will work, and the responsibilities of each user group. The goal is to provide a straightforward, non-technical understanding of the platform.

---

## 1. Purpose of the Website

The **Udoy platform** is a digital learning space created to empower underprivileged children in **Classes 6 to 8**. It aims to provide structured, high-quality education to help them build strong academic foundations and life skills. The platform is **lightweight, simple, and accessible**, ensuring smooth use on basic devices and low internet connections. Students can access lessons, quizzes, and guidance from coaches and mentors.

---

## 2. User Groups and Their Activities

Each user role on the platform plays a specific part in the learning ecosystem. Sponsors donate credits, which are distributed as rewards for course completion. Coaches guide students and allocate additional credits. Content Creators develop learning material, Validators ensure its quality, and Admins coordinate overall operations.

- **Sponsors:** Donate credits that are awarded to students.
- **Students:** Learn through structured content and track their progress.
- **Content Creators:** Ex-students who create and upload learning materials.
- **Validators:** Ex-teachers who review and approve content.
- **Coaches:** Monitor progress, guide learners, and manage credit allocations.
- **Admins:** Manage users, courses, content, and platform-wide settings.

---

## 3. Udoy Key Features by User Role

### Students

- Sign up, verify email, and log in.
- Manage personal profiles.
- Browse and enroll in courses.
- Watch video lessons.
- Track learning progress with per-course trackers showing completion, quiz scores, and resume points.
- Take quizzes.
- Receive certificates upon course completion.
- View a personalized dashboard.

### Content Creators

- Sign up, verify email, and log in.
- Manage profiles and create courses.
- Add lessons with multiple media formats (videos, text, audio).
- Create and manage quizzes.
- Monitor student enrollment and track performance.
- Issue certificates and view basic analytics.

### Validators

- Review content submitted by creators.
- Approve, reject, or suggest edits.
- Ensure content quality and accuracy.

### Coaches

- Monitor student activity and performance.
- Provide guidance and motivation.
- Identify students who need extra support.
- Organize approved topics into chapters and align them with subjects.
- Allocate credits to students based on performance and engagement.

### Admins

- Manage users (view, edit, deactivate, delete).
- Assign or modify user roles.
- Moderate content and view activity logs.
- Access platform-wide analytics and reports.
- Control platform settings and permissions.
- Oversee course structure, user engagement, and credit flow.

### Sponsors

- Donate credits to the platform.
- View credit distribution and usage.
- Track how their contributions reward students.

---

## 4. What the Website Will Do

- Provide secure, role-based access for all users.
- Allow students to browse subjects, watch lessons, and complete quizzes.
- Offer per-course progress tracking.
- Enable creators to upload and organize lessons, activities, and quizzes.
- Allow validators to review and approve content.
- Enable coaches to monitor and support student progress.
- Give admins full control over users, courses, content, credit management, notifications, and overall platform operations.

---

## 5. How It Will Work

The **Admin** role is central to coordinating activities. Admins oversee user accounts, course structures, credit flow, platform settings, and engagement.

### 1. Content Creation Flow

- Content Creators develop individual topics.
- Validators review, correct, approve, or reject topics.
- Coaches combine approved topics into chapters and align them with subjects.
- Multiple subjects are grouped together to form a complete course.
- Once structured, the course becomes available to students.

### 2. Student Learning Flow

- Students log in, browse subjects, and access lessons.
- They learn through various media and take quizzes.
- Their progress is tracked automatically.
- Upon course completion, credits are awarded and milestones celebrated.

### 3. Credit Distribution Flow

- Sponsors donate credits to the platform.
- Credits are automatically distributed to students upon course completion.
- Coaches have a pool of credits to reward performance.
- Sponsors can track how their credits are used.

### 4. Notification Flow

- Email notifications are sent to relevant users when key events occur (e.g., course completion, content approvals, credit awards).
- Future support can include SMS or in-app notifications.

### 5. Admin Flow

- Admins manage users, content, credits, notifications, and platform settings.
- Admins ensure smooth operations and monitor engagement through analytics.

---

## 6. Key Systems

### Content Recommendation Engine

- Personalizes learning paths for students.
- Recommends next courses based on completed ones.
- Suggests extra practice or remedial content.
- Highlights trending or popular lessons.
- Integrates with gamification and credit systems.

### Gamification System

- Encourages engagement through badges, levels, streaks, and leaderboards.
- Celebrates milestones like first course completed or top quiz scores.
- Integrates with credit rewards to keep students motivated.

### Notification System

- Sends important updates and alerts via email.
- Notifies students, creators, validators, coaches, sponsors, and admins of relevant activities.
- Can be expanded in the future to support other channels.

### User Management System

- Admins manage user accounts for all roles.
- Supports creating, editing, deactivating, and deleting users.
- Includes role assignments and permissions.
- Tracks user activity and ensures data privacy.

### Credit Management System

- Sponsors donate credits to a central pool.
- Credits are automatically awarded when students complete courses.
- Coaches can allocate additional credits to students.
- Admins oversee credit distribution and ensure transparency.

### Analytics & Reporting System

- Provides actionable insights for decision-making.
- Admin dashboard shows platform-wide engagement.
- Coach dashboard displays student progress.
- Sponsor reports show credit impact.
- Tracks course completion rates, quiz performance, and activity trends.

### Feedback & Support System

- Students can rate lessons and provide quick feedback.
- Creators and validators can flag issues.
- A built-in help center or chatbot addresses common FAQs.
- Admins use feedback analytics to improve usability and content quality.

### Offline Access / Low-Bandwidth Optimization

- Supports students with poor connectivity.
- Lessons and quizzes can be downloaded for offline use.
- Progress syncs automatically when online.
- Lightweight compression improves performance.

### Compliance & Safety Systems

- Protects student safety and data privacy.
- Includes role-based access and parental consent mechanisms.
- Aligns with GDPR-like privacy standards.
- Provides content moderation tools and security monitoring.

### Version Control for Content

- Tracks all content changes.
- Maintains version history with changelogs.
- Supports draft and published states.
- Allows rollback if needed.

### Course Management System

- Content Creators develop topics with multiple media formats.
- Every topic must include at least one quiz.
- Validators review and approve content.
- Coaches structure chapters and subjects.
- Multiple subjects form a complete course.
- Admins control course structure, visibility, and availability.

---

## 7. Platform Features Summary

- Simple, secure login for all roles.
- Clean, intuitive subject and lesson navigation.
- Interactive quizzes and assignments.
- Progress tracking per course.
- Integrated credit, gamification, and recommendation systems.
- Role-specific dashboards for students, coaches, sponsors, and admins.
- Comprehensive content and user management.

---

## 8. Basic Rules

- All lessons must be approved before publication.
- Student data and activity must remain private and secure.
- The platform must remain easy to use for children with minimal digital experience.
- Admins are responsible for monitoring, maintaining, and ensuring platform integrity.

---

## 9. Summary

The **Udoy platform** functions as a **digital school** where:

- Students learn through structured lessons and track their progress.
- Ex-students create content.
- Validators ensure content quality.
- Coaches guide learners and allocate credits.
- Sponsors support the ecosystem.
- Admins maintain and manage the platform.

---

## Running the Reference Implementation

This repository now includes a fully working FastAPI backend that models the complete Udoy platform experience described above. The implementation lives under the `app/` package and persists data to a local SQLite database (`udoy.db`).

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the API server

```bash
uvicorn app.main:app --reload
```

The API is documented automatically at `http://127.0.0.1:8000/docs` where you can try every endpoint interactively.

### 3. Seed data and roles

On first launch the application seeds an administrator account:

- **Email:** `admin@udoy.local`
- **Password:** `admin123`

Use this account to approve content, manage roles, or publish courses.

### 4. Feature coverage by role

| Role | Highlights |
| --- | --- |
| Students | Register/login, enroll, attempt quizzes, receive certificates & credits, leave lesson feedback, see personalized dashboard, notifications, and smart recommendations. |
| Content Creators | Build courses/lessons/quizzes, submit for validation, track enrollments, inspect feedback, and review performance insights for their catalog. |
| Validators | Approve or reject lessons with feedback and monitor pending submissions. |
| Coaches | Organize chapters, assign lessons, view every student’s trajectory, and allocate sponsor-backed credits. |
| Sponsors | Donate credits and read transparent credit impact reports. |
| Admins | Manage users/roles, publish courses, inspect analytics, and audit activity logs and credit pools. |

All major subsystems from the specification—including gamification badges, content approval workflow, credit distribution, notifications, analytics dashboards, recommendation engine, and versioned activity logging—are represented in the API.

