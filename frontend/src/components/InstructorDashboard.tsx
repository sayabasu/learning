import React, { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { generateId } from '../utils';
import { useAuth } from '../contexts/AuthContext';
import { useData } from '../contexts/DataContext';
import type { Course, Lesson, Module } from '../types';

interface CourseDraft extends Omit<Course, 'id' | 'createdAt' | 'modules'> {
  modules: Module[];
}

const emptyDraft: CourseDraft = {
  title: '',
  category: '',
  description: '',
  duration: '2h',
  level: 'Beginner',
  instructorId: '',
  tags: [],
  modules: []
};

dayjs.extend(relativeTime);

const InstructorDashboard: React.FC = () => {
  const { user } = useAuth();
  const {
    courses,
    enrollments,
    learnersForCourse,
    createCourse,
    addModule,
    addLesson,
    submitAssignment
  } = useData();
  const [draft, setDraft] = useState<CourseDraft>({ ...emptyDraft, instructorId: user?.id ?? '' });
  const [activeCourse, setActiveCourse] = useState<string | null>(courses[0]?.id ?? null);
  const [moduleTitle, setModuleTitle] = useState('');
  const [moduleDescription, setModuleDescription] = useState('');
  const [lesson, setLesson] = useState<Partial<Lesson>>({ contentType: 'video' });

  const instructorCourses = useMemo(
    () => courses.filter((course) => course.instructorId === user?.id),
    [courses, user?.id]
  );

  const selectedCourse = instructorCourses.find((course) => course.id === activeCourse);

  const handleCreateCourse = (event: React.FormEvent) => {
    event.preventDefault();
    if (!user) return;
    if (!draft.title.trim()) return;

    createCourse({
      ...draft,
      instructorId: user.id,
      modules: [],
      tags: draft.tags.length ? draft.tags : ['New'],
      description: draft.description.trim() || 'Curated learning journey awaiting content.'
    });

    setDraft({ ...emptyDraft, instructorId: user.id });
  };

  const handleAddModule = (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedCourse) return;

    addModule(selectedCourse.id, {
      id: generateId(),
      title: moduleTitle,
      description: moduleDescription,
      lessons: []
    });

    setModuleTitle('');
    setModuleDescription('');
  };

  const handleAddLesson = (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedCourse || !selectedCourse.modules.length) return;
    const targetModule = selectedCourse.modules[selectedCourse.modules.length - 1];

    addLesson(selectedCourse.id, targetModule.id, {
      id: generateId(),
      title: lesson.title ?? 'Untitled lesson',
      contentType: (lesson.contentType as Lesson['contentType']) ?? 'video',
      description: lesson.description ?? 'Lesson description coming soon.',
      resourceUrl: lesson.resourceUrl,
      quiz: lesson.quiz
    });

    setLesson({ contentType: 'video' });
  };

  const handleQuickGrade = (lessonId: string, learnerId: string) => {
    submitAssignment({
      id: `${lessonId}-${learnerId}`,
      lessonId,
      learnerId,
      submittedAt: new Date().toISOString(),
      status: 'graded',
      grade: 95,
      feedback: 'Beautiful insight! You connected learner needs to tangible prototypes.'
    });
  };

  return (
    <section className="grid" style={{ gap: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', color: '#0f172a' }}>Creator studio</h1>
          <p style={{ color: '#475569', marginTop: '0.4rem' }}>
            Build experiences, watch learners engage, and iterate together in real time.
          </p>
        </div>
        <select
          value={activeCourse ?? ''}
          onChange={(event) => setActiveCourse(event.target.value || null)}
          style={{ padding: '0.6rem 0.75rem', borderRadius: '0.75rem' }}
        >
          {instructorCourses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.title}
            </option>
          ))}
          {!instructorCourses.length && <option value="">No courses yet</option>}
        </select>
      </div>

      <div className="grid grid-2">
        <form className="card form" onSubmit={handleCreateCourse}>
          <h3>Create a new course</h3>
          <label>
            Title
            <input
              value={draft.title}
              onChange={(event) => setDraft((prev) => ({ ...prev, title: event.target.value }))}
              placeholder="Learning Experience Design Sprint"
              required
            />
          </label>
          <label>
            Category
            <input
              value={draft.category}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, category: event.target.value }))
              }
              placeholder="Learning Strategy"
            />
          </label>
          <label>
            Description
            <textarea
              value={draft.description}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, description: event.target.value }))
              }
            />
          </label>
          <label>
            Level
            <select
              value={draft.level}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, level: event.target.value as Course['level'] }))
              }
            >
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </label>
          <label>
            Duration
            <input
              value={draft.duration}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, duration: event.target.value }))
              }
              placeholder="3h"
            />
          </label>
          <label>
            Tags
            <input
              value={draft.tags.join(', ')}
              onChange={(event) =>
                setDraft((prev) => ({
                  ...prev,
                  tags: event.target.value.split(',').map((tag) => tag.trim()).filter(Boolean)
                }))
              }
              placeholder="Design, Research, Facilitation"
            />
          </label>
          <button className="btn-primary" type="submit">
            Publish course
          </button>
        </form>

        <div className="card">
          <h3>Active learners</h3>
          <div className="list" style={{ marginTop: '1rem' }}>
            {selectedCourse ? (
              learnersForCourse(selectedCourse.id).map((learner) => {
                const enrollment = enrollments.find(
                  (item) => item.learnerId === learner.id && item.courseId === selectedCourse.id
                );
                const progress = enrollment && selectedCourse
                  ? Math.round(
                      (enrollment.completedLessons.length /
                        selectedCourse.modules.flatMap((module) => module.lessons).length) *
                        100
                    )
                  : 0;
                return (
                  <div key={learner.id} className="list-item">
                    <div>
                      <strong>{learner.name}</strong>
                      <p style={{ margin: '0.3rem 0 0', color: '#475569', fontSize: '0.8rem' }}>
                        Joined {enrollment ? dayjs(enrollment.enrolledAt).fromNow() : 'recently'}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className="badge">{progress}%</div>
                      <button
                        className="btn-ghost"
                        style={{ marginTop: '0.5rem' }}
                        type="button"
                        onClick={() => handleQuickGrade('l-2', learner.id)}
                      >
                        Send feedback
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="empty-state">
                <strong>Select a course</strong>
                <span>Pick one of your experiences to review learner engagement.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedCourse && (
        <div className="card">
          <h3>Modules & lessons</h3>
          <div className="grid grid-2" style={{ marginTop: '1rem' }}>
            {selectedCourse.modules.map((module) => (
              <div key={module.id} className="card" style={{ boxShadow: 'none', border: '1px solid rgba(148,163,184,0.2)' }}>
                <strong>{module.title}</strong>
                <p style={{ color: '#64748b', marginTop: '0.25rem' }}>{module.description}</p>
                <ul style={{ paddingLeft: '1rem', color: '#475569', lineHeight: 1.6 }}>
                  {module.lessons.map((moduleLesson) => (
                    <li key={moduleLesson.id}>
                      {moduleLesson.title} · <span style={{ color: '#94a3b8' }}>{moduleLesson.contentType}</span>
                    </li>
                  ))}
                  {!module.lessons.length && <li>No lessons yet. Add one below.</li>}
                </ul>
              </div>
            ))}
            {!selectedCourse.modules.length && (
              <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                <strong>No modules yet</strong>
                <span>Add your first module to map the journey.</span>
              </div>
            )}
          </div>

          <div className="grid grid-2" style={{ marginTop: '1.5rem' }}>
            <form className="form card" style={{ boxShadow: 'none' }} onSubmit={handleAddModule}>
              <h4 style={{ marginTop: 0 }}>Add module</h4>
              <label>
                Title
                <input
                  value={moduleTitle}
                  onChange={(event) => setModuleTitle(event.target.value)}
                  placeholder="Prototyping sprints"
                  required
                />
              </label>
              <label>
                Description
                <textarea
                  value={moduleDescription}
                  onChange={(event) => setModuleDescription(event.target.value)}
                  placeholder="Outline what learners will achieve here"
                />
              </label>
              <button className="btn-primary" type="submit">
                Add module
              </button>
            </form>

            <form className="form card" style={{ boxShadow: 'none' }} onSubmit={handleAddLesson}>
              <h4 style={{ marginTop: 0 }}>Add lesson</h4>
              <label>
                Title
                <input
                  value={lesson.title ?? ''}
                  onChange={(event) => setLesson((prev) => ({ ...prev, title: event.target.value }))}
                  placeholder="Rapid prototyping demo"
                />
              </label>
              <label>
                Type
                <select
                  value={lesson.contentType ?? 'video'}
                  onChange={(event) =>
                    setLesson((prev) => ({ ...prev, contentType: event.target.value as Lesson['contentType'] }))
                  }
                >
                  <option value="video">Video</option>
                  <option value="pdf">PDF</option>
                  <option value="text">Article</option>
                  <option value="quiz">Quiz</option>
                  <option value="assignment">Assignment</option>
                </select>
              </label>
              <label>
                Description
                <textarea
                  value={lesson.description ?? ''}
                  onChange={(event) =>
                    setLesson((prev) => ({ ...prev, description: event.target.value }))
                  }
                  placeholder="Share context, duration, and expected outcomes"
                />
              </label>
              <label>
                Resource URL (optional)
                <input
                  value={lesson.resourceUrl ?? ''}
                  onChange={(event) =>
                    setLesson((prev) => ({ ...prev, resourceUrl: event.target.value }))
                  }
                  placeholder="https://"
                />
              </label>
              <button className="btn-primary" type="submit">
                Add lesson
              </button>
            </form>
          </div>
        </div>
      )}
    </section>
  );
};

export default InstructorDashboard;
