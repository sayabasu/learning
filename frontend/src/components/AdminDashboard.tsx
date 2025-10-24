import React, { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import { useAuth } from '../contexts/AuthContext';
import { useData } from '../contexts/DataContext';
import type { Announcement, Role } from '../types';

interface AdminDashboardProps {
  onComposeAnnouncement: () => void;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ onComposeAnnouncement }) => {
  const { users } = useAuth();
  const { courses, enrollments, announcements, activeRoleFilter, setActiveRoleFilter } = useData();
  const [tab, setTab] = useState<'overview' | 'people' | 'activity'>('overview');

  const stats = useMemo(() => {
    const totalLearners = users.filter((user) => user.role === 'learner').length;
    const activeCourses = courses.length;
    const completions = enrollments.filter((enrollment) => Boolean(enrollment.completedAt)).length;
    return { totalLearners, activeCourses, completions };
  }, [users, courses, enrollments]);

  const filteredUsers = useMemo(() => {
    if (activeRoleFilter === 'all') return users;
    return users.filter((user) => user.role === activeRoleFilter);
  }, [users, activeRoleFilter]);

  return (
    <section className="grid" style={{ gap: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', color: '#0f172a' }}>Welcome back, Admin</h1>
          <p style={{ color: '#475569', marginTop: '0.4rem' }}>
            Track adoption, enroll new teams, and share campus-wide announcements.
          </p>
        </div>
        <button className="btn-primary" onClick={onComposeAnnouncement} type="button">
          + New announcement
        </button>
      </div>

      <div className="grid grid-3">
        <div className="card stat-card">
          <span className="badge">Learners</span>
          <div className="stat-value">{stats.totalLearners}</div>
          <p>Active learners discovering pathways this week.</p>
        </div>
        <div className="card stat-card">
          <span className="badge">Courses</span>
          <div className="stat-value">{stats.activeCourses}</div>
          <p>Curated experiences available across your academy.</p>
        </div>
        <div className="card stat-card">
          <span className="badge">Certificates</span>
          <div className="stat-value">{stats.completions}</div>
          <p>Celebrated journeys that reached the finish line.</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <div className="tab-bar">
          {(['overview', 'people', 'activity'] as const).map((tabKey) => (
            <button
              key={tabKey}
              className={tabKey === tab ? 'active' : ''}
              onClick={() => setTab(tabKey)}
              type="button"
            >
              {tabKey === 'overview' && 'Overview'}
              {tabKey === 'people' && 'People'}
              {tabKey === 'activity' && 'Announcements'}
            </button>
          ))}
        </div>
        {tab === 'people' && (
          <select
            value={activeRoleFilter}
            onChange={(event) => setActiveRoleFilter(event.target.value as Role | 'all')}
            style={{ padding: '0.6rem 0.75rem', borderRadius: '0.75rem' }}
          >
            <option value="all">All roles</option>
            <option value="admin">Admins</option>
            <option value="instructor">Instructors</option>
            <option value="learner">Learners</option>
          </select>
        )}
      </div>

      {tab === 'overview' && (
        <div className="grid grid-2">
          <div className="card">
            <h3>Popular courses</h3>
            <div className="list" style={{ marginTop: '1.25rem' }}>
              {courses.map((course) => {
                const activeLearners = enrollments.filter(
                  (enrollment) => enrollment.courseId === course.id
                );
                const completionRate = activeLearners.length
                  ? Math.round(
                      (activeLearners.filter((enrollment) => enrollment.completedAt).length /
                        activeLearners.length) *
                        100
                    )
                  : 0;
                return (
                  <div key={course.id} className="list-item">
                    <div>
                      <strong>{course.title}</strong>
                      <p style={{ margin: '0.25rem 0 0', color: '#64748b', fontSize: '0.85rem' }}>
                        {course.level} · {course.duration}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className="badge">{activeLearners.length} enrolled</span>
                      <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: '#475569' }}>
                        {completionRate}% completion
                      </p>
                    </div>
                  </div>
                );
              })}
              {!courses.length && (
                <div className="empty-state">
                  <strong>No courses yet</strong>
                  <span>Instructors can start by creating a new learning pathway.</span>
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <h3>Recent enrollment activity</h3>
            <table className="table" style={{ marginTop: '1rem' }}>
              <thead>
                <tr>
                  <th>Learner</th>
                  <th>Course</th>
                  <th>Progress</th>
                </tr>
              </thead>
              <tbody>
                {enrollments.slice(0, 6).map((enrollment) => {
                  const learner = users.find((user) => user.id === enrollment.learnerId);
                  const course = courses.find((c) => c.id === enrollment.courseId);
                  const progress = course
                    ? Math.round(
                        (enrollment.completedLessons.length /
                          course.modules.flatMap((module) => module.lessons).length) *
                          100
                      )
                    : 0;
                  return (
                    <tr key={enrollment.id}>
                      <td>{learner?.name ?? 'Learner'}</td>
                      <td>{course?.title ?? 'Course removed'}</td>
                      <td>
                        <div className="progress-bar">
                          <span style={{ width: `${progress}%` }} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {!enrollments.length && (
                  <tr>
                    <td colSpan={3} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                      No enrollment data yet. As learners join courses, their progress will land here.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'people' && (
        <div className="card">
          <h3>People</h3>
          <table className="table" style={{ marginTop: '1rem' }}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className="badge">{user.role}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'activity' && (
        <div className="card">
          <h3>Announcements</h3>
          <div className="list" style={{ marginTop: '1rem' }}>
            {announcements.map((announcement: Announcement) => (
              <div key={announcement.id} className="list-item" style={{ alignItems: 'flex-start' }}>
                <div>
                  <strong>{announcement.title}</strong>
                  <p style={{ margin: '0.35rem 0 0', color: '#475569' }}>{announcement.message}</p>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {dayjs(announcement.createdAt).format('MMM D, YYYY · h:mm a')}
                  </span>
                </div>
                <span className="badge">{announcement.target}</span>
              </div>
            ))}
            {!announcements.length && (
              <div className="empty-state">
                <strong>No announcements yet</strong>
                <span>Start the conversation with a welcome note to your learners.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
};

export default AdminDashboard;
