import React, { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import { useAuth } from '../contexts/AuthContext';
import { useData } from '../contexts/DataContext';
import type { Course, Lesson } from '../types';

const LearnerDashboard: React.FC = () => {
  const { user } = useAuth();
  const {
    courses,
    enrollments,
    announcements,
    certificates,
    toggleLessonCompletion
  } = useData();
  const learnerEnrollments = useMemo(
    () => enrollments.filter((enrollment) => enrollment.learnerId === user?.id),
    [enrollments, user?.id]
  );
  const [activeCourseId, setActiveCourseId] = useState<string | null>(
    learnerEnrollments[0]?.courseId ?? null
  );
  const [quizState, setQuizState] = useState<Record<string, string>>({});
  const [quizFeedback, setQuizFeedback] = useState<Record<string, string>>({});

  const activeEnrollment = learnerEnrollments.find(
    (enrollment) => enrollment.courseId === activeCourseId
  );

  const activeCourse: Course | undefined = courses.find((course) => course.id === activeCourseId);

  const progress = useMemo(() => {
    if (!activeCourse || !activeEnrollment) return 0;
    const totalLessons = activeCourse.modules.flatMap((module) => module.lessons).length;
    if (!totalLessons) return 0;
    return Math.round((activeEnrollment.completedLessons.length / totalLessons) * 100);
  }, [activeCourse, activeEnrollment]);

  const handleToggleLesson = (lesson: Lesson) => {
    if (!activeEnrollment) return;
    toggleLessonCompletion(activeEnrollment.id, lesson.id);
    setQuizFeedback((prev) => ({ ...prev, [lesson.id]: '' }));
  };

  const handleQuizSubmit = (lesson: Lesson) => {
    if (!lesson.quiz || !lesson.quiz.length || !activeEnrollment) return;
    const selected = quizState[lesson.id];
    const correct = lesson.quiz[0].answer;

    if (!selected) {
      setQuizFeedback((prev) => ({ ...prev, [lesson.id]: 'Select an option to continue.' }));
      return;
    }

    if (selected === correct) {
      toggleLessonCompletion(activeEnrollment.id, lesson.id);
      setQuizFeedback((prev) => ({ ...prev, [lesson.id]: 'Great job! Lesson completed.' }));
    } else {
      setQuizFeedback((prev) => ({ ...prev, [lesson.id]: 'Try again — revisit the lesson notes.' }));
    }
  };

  return (
    <section className="grid" style={{ gap: '2rem' }}>
      <div className="grid grid-2">
        <div className="card">
          <h3>Learning streak</h3>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span className="stat-value" style={{ fontSize: '2.5rem' }}>
              {progress}%
            </span>
            <span style={{ color: '#475569' }}>current course completion</span>
          </div>
          <div className="progress-bar" style={{ marginTop: '1rem' }}>
            <span style={{ width: `${progress}%` }} />
          </div>
          {activeEnrollment?.completedAt && (
            <p style={{ color: '#22c55e', marginTop: '0.75rem', fontWeight: 600 }}>
              Course completed on {dayjs(activeEnrollment.completedAt).format('MMM D, YYYY')}.
            </p>
          )}
        </div>

        <div className="card">
          <h3>Announcements</h3>
          <ul style={{ margin: '1rem 0 0', padding: 0, listStyle: 'none', color: '#475569' }}>
            {announcements.slice(0, 3).map((announcement) => (
              <li key={announcement.id} style={{ marginBottom: '0.75rem' }}>
                <strong style={{ color: '#0f172a' }}>{announcement.title}</strong>
                <p style={{ margin: '0.35rem 0 0' }}>{announcement.message}</p>
              </li>
            ))}
            {!announcements.length && <li>No announcements yet.</li>}
          </ul>
        </div>
      </div>

      <div className="card">
        <h3>My courses</h3>
        <div className="course-list" style={{ marginTop: '1.25rem' }}>
          {learnerEnrollments.map((enrollment) => {
            const course = courses.find((item) => item.id === enrollment.courseId);
            if (!course) return null;
            const totalLessons = course.modules.flatMap((module) => module.lessons).length;
            const courseProgress = totalLessons
              ? Math.round((enrollment.completedLessons.length / totalLessons) * 100)
              : 0;
            const isCompleted = Boolean(enrollment.completedAt);

            return (
              <div key={enrollment.id} className="card course-card">
                <div>
                  <span className="badge">{course.level}</span>
                  <h3 style={{ marginTop: '0.75rem' }}>{course.title}</h3>
                  <p>{course.description}</p>
                </div>
                <div>
                  <div className="progress-bar">
                    <span style={{ width: `${courseProgress}%` }} />
                  </div>
                  <p style={{ color: '#475569', marginTop: '0.35rem', fontSize: '0.85rem' }}>
                    {courseProgress}% complete · {course.duration}
                  </p>
                </div>
                <footer>
                  <button
                    className="btn-ghost"
                    type="button"
                    onClick={() => setActiveCourseId(enrollment.courseId)}
                  >
                    {activeCourseId === enrollment.courseId ? 'Viewing' : 'View course'}
                  </button>
                  {isCompleted && certificates[user?.id ?? '']?.includes(course.id) && (
                    <div className="badge" style={{ background: 'rgba(34,197,94,0.15)', color: '#15803d' }}>
                      Certificate ready
                    </div>
                  )}
                </footer>
              </div>
            );
          })}
          {!learnerEnrollments.length && (
            <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
              <strong>No courses yet</strong>
              <span>Your instructor will invite you to your first learning journey shortly.</span>
            </div>
          )}
        </div>
      </div>

      {activeCourse && activeEnrollment && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3>{activeCourse.title}</h3>
              <p style={{ color: '#475569', marginTop: '0.35rem' }}>{activeCourse.description}</p>
            </div>
            {certificates[user?.id ?? '']?.includes(activeCourse.id) && (
              <div className="badge" style={{ background: 'rgba(37,99,235,0.12)', color: '#1d4ed8' }}>
                🎉 Certificate issued
              </div>
            )}
          </div>

          <div style={{ marginTop: '1.5rem' }}>
            {activeCourse.modules.map((module) => (
              <div key={module.id} style={{ marginBottom: '1.5rem' }}>
                <strong style={{ color: '#0f172a' }}>{module.title}</strong>
                <p style={{ color: '#64748b', marginTop: '0.3rem' }}>{module.description}</p>
                <div className="list" style={{ marginTop: '0.75rem' }}>
                  {module.lessons.map((lesson) => {
                    const completed = activeEnrollment.completedLessons.includes(lesson.id);
                    return (
                      <div key={lesson.id} className="list-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.75rem' }}>
                        <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                          <div>
                            <strong>{lesson.title}</strong>
                            <p style={{ margin: '0.25rem 0 0', color: '#64748b', fontSize: '0.85rem' }}>
                              {lesson.description}
                            </p>
                          </div>
                          <span className="badge">{lesson.contentType}</span>
                        </div>
                        {lesson.contentType === 'quiz' && lesson.quiz && (
                          <div style={{ width: '100%' }}>
                            <p style={{ color: '#475569', margin: '0.25rem 0' }}>
                              {lesson.quiz[0].prompt}
                            </p>
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                              {lesson.quiz[0].options.map((option) => (
                                <button
                                  key={option}
                                  type="button"
                                  onClick={() => setQuizState((prev) => ({ ...prev, [lesson.id]: option }))}
                                  className="btn-ghost"
                                  style={{
                                    background:
                                      quizState[lesson.id] === option
                                        ? 'rgba(37,99,235,0.15)'
                                        : 'rgba(148,163,184,0.15)',
                                    borderColor:
                                      quizState[lesson.id] === option
                                        ? 'rgba(37,99,235,0.4)'
                                        : 'transparent'
                                  }}
                                >
                                  {option}
                                </button>
                              ))}
                            </div>
                            <button
                              className="btn-primary"
                              type="button"
                              style={{ marginTop: '0.75rem' }}
                              onClick={() => handleQuizSubmit(lesson)}
                            >
                              Submit answer
                            </button>
                            {quizFeedback[lesson.id] && (
                              <p
                                style={{
                                  marginTop: '0.5rem',
                                  color: quizFeedback[lesson.id].includes('Great') ? '#16a34a' : '#dc2626'
                                }}
                              >
                                {quizFeedback[lesson.id]}
                              </p>
                            )}
                          </div>
                        )}
                        <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between' }}>
                          {lesson.resourceUrl && (
                            <a
                              href={lesson.resourceUrl}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#2563eb', fontWeight: 500 }}
                            >
                              View resource
                            </a>
                          )}
                          <button
                            className="btn-ghost"
                            type="button"
                            onClick={() => handleToggleLesson(lesson)}
                            style={{ background: completed ? 'rgba(34,197,94,0.15)' : undefined }}
                          >
                            {completed ? 'Completed' : 'Mark complete'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

export default LearnerDashboard;
