import React, { createContext, useContext, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import type {
  Announcement,
  AssignmentSubmission,
  Course,
  Enrollment,
  Lesson,
  Module,
  Role,
  User
} from '../types';
import { useAuth } from './AuthContext';
import { generateId } from '../utils';

type DataContextValue = {
  courses: Course[];
  enrollments: Enrollment[];
  announcements: Announcement[];
  certificates: Record<string, string[]>;
  submissions: AssignmentSubmission[];
  createCourse: (payload: Omit<Course, 'id' | 'createdAt'>) => void;
  addModule: (courseId: string, module: Module) => void;
  addLesson: (courseId: string, moduleId: string, lesson: Lesson) => void;
  enrollLearner: (courseId: string, learnerId: string) => void;
  toggleLessonCompletion: (enrollmentId: string, lessonId: string) => void;
  issueCertificate: (courseId: string, learnerId: string) => void;
  submitAssignment: (submission: AssignmentSubmission) => void;
  recordAnnouncement: (announcement: Omit<Announcement, 'id' | 'createdAt'>) => void;
  learnersForCourse: (courseId: string) => User[];
  progressForEnrollment: (enrollment: Enrollment, course: Course) => number;
  activeRoleFilter: Role | 'all';
  setActiveRoleFilter: (role: Role | 'all') => void;
};

const DataContext = createContext<DataContextValue | undefined>(undefined);

const seedCourses = (instructorId: string): Course[] => [
  {
    id: 'c-design-thinking',
    title: 'Design Thinking Foundations',
    category: 'Product Design',
    description:
      'Learn how to craft learner-centric experiences with empathy mapping, ideation frameworks, and rapid prototyping.',
    instructorId,
    duration: '4h 30m',
    level: 'Beginner',
    tags: ['Innovation', 'Creativity'],
    createdAt: dayjs().subtract(10, 'day').toISOString(),
    modules: [
      {
        id: 'm-1',
        title: 'Empathy & Research',
        description: 'Understand your learners and capture true needs.',
        lessons: [
          {
            id: 'l-1',
            title: 'Observational Research',
            contentType: 'video',
            description: 'A 12-minute walkthrough on shadowing techniques.',
            resourceUrl: 'https://www.loom.com/share/design-thinking-observation'
          },
          {
            id: 'l-2',
            title: 'Problem Statements',
            contentType: 'assignment',
            description: 'Upload your POV statement for peer review.'
          },
          {
            id: 'l-3',
            title: 'Empathy Quiz',
            contentType: 'quiz',
            description: 'Short check-in on empathy methods.',
            quiz: [
              {
                id: 'q-1',
                prompt: 'Which artefact best captures a learner need?',
                options: ['Interview recording', 'Persona empathy map', 'Survey link', 'Course outline'],
                answer: 'Persona empathy map'
              }
            ]
          }
        ]
      }
    ]
  }
];

const defaultAnnouncements: Announcement[] = [
  {
    id: 'a-1',
    title: '✨ PulseLearn launch week',
    message: 'Thanks for joining our beta! Expect new studios and live cohorts rolling out weekly.',
    createdAt: dayjs().subtract(1, 'day').toISOString(),
    authorId: 'u-admin',
    target: 'all'
  }
];

export const DataProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const { users } = useAuth();
  const instructor = users.find((u) => u.role === 'instructor');
  const [courses, setCourses] = useState<Course[]>(seedCourses(instructor?.id ?? 'u-mentor'));
  const [enrollments, setEnrollments] = useState<Enrollment[]>([
    {
      id: 'enroll-1',
      courseId: 'c-design-thinking',
      learnerId: 'u-learner',
      enrolledAt: dayjs().subtract(2, 'day').toISOString(),
      completedLessons: ['l-1'],
      completedAt: undefined
    }
  ]);
  const [announcements, setAnnouncements] = useState<Announcement[]>(defaultAnnouncements);
  const [certificates, setCertificates] = useState<Record<string, string[]>>({ 'u-learner': [] });
  const [submissions, setSubmissions] = useState<AssignmentSubmission[]>([]);
  const [activeRoleFilter, setActiveRoleFilter] = useState<Role | 'all'>('all');

  const createCourse: DataContextValue['createCourse'] = (payload) => {
    setCourses((prev) => [
      {
        ...payload,
        id: generateId(),
        createdAt: new Date().toISOString()
      },
      ...prev
    ]);
  };

  const addModule = (courseId: string, module: Module) => {
    setCourses((prev) =>
      prev.map((course) =>
        course.id === courseId
          ? { ...course, modules: [...course.modules, module] }
          : course
      )
    );
  };

  const addLesson = (courseId: string, moduleId: string, lesson: Lesson) => {
    setCourses((prev) =>
      prev.map((course) =>
        course.id === courseId
          ? {
              ...course,
              modules: course.modules.map((module) =>
                module.id === moduleId
                  ? { ...module, lessons: [...module.lessons, lesson] }
                  : module
              )
            }
          : course
      )
    );
  };

  const enrollLearner = (courseId: string, learnerId: string) => {
    const exists = enrollments.some(
      (enrollment) => enrollment.courseId === courseId && enrollment.learnerId === learnerId
    );
    if (exists) return;

    setEnrollments((prev) => [
      ...prev,
      {
        id: generateId(),
        courseId,
        learnerId,
        enrolledAt: new Date().toISOString(),
        completedLessons: []
      }
    ]);
  };

  const toggleLessonCompletion = (enrollmentId: string, lessonId: string) => {
    setEnrollments((prev) =>
      prev.map((enrollment) => {
        if (enrollment.id !== enrollmentId) return enrollment;

        const already = enrollment.completedLessons.includes(lessonId);
        const updatedLessons = already
          ? enrollment.completedLessons.filter((id) => id !== lessonId)
          : [...enrollment.completedLessons, lessonId];

        const course = courses.find((c) => c.id === enrollment.courseId);
        const totalLessons = course?.modules.flatMap((m) => m.lessons).length ?? 0;
        const completedAt =
          totalLessons > 0 && updatedLessons.length === totalLessons
            ? new Date().toISOString()
            : undefined;

        if (completedAt) {
          setCertificates((prevCerts) => {
            const existing = prevCerts[enrollment.learnerId] ?? [];
            if (existing.includes(enrollment.courseId)) return prevCerts;
            return {
              ...prevCerts,
              [enrollment.learnerId]: [...existing, enrollment.courseId]
            };
          });
        }

        return {
          ...enrollment,
          completedLessons: updatedLessons,
          completedAt
        };
      })
    );
  };

  const issueCertificate = (courseId: string, learnerId: string) => {
    setCertificates((prev) => {
      const current = prev[learnerId] ?? [];
      if (current.includes(courseId)) return prev;
      return {
        ...prev,
        [learnerId]: [...current, courseId]
      };
    });
  };

  const submitAssignment = (submission: AssignmentSubmission) => {
    setSubmissions((prev) => {
      const existingIndex = prev.findIndex((item) => item.id === submission.id);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = submission;
        return updated;
      }
      return [...prev, submission];
    });
  };

  const recordAnnouncement = (announcement: Omit<Announcement, 'id' | 'createdAt'>) => {
    setAnnouncements((prev) => [
      {
        ...announcement,
        id: generateId(),
        authorId: announcement.authorId ?? 'system',
        createdAt: new Date().toISOString()
      },
      ...prev
    ]);
  };

  const learnersForCourse = (courseId: string) => {
    const learnerIds = enrollments
      .filter((enrollment) => enrollment.courseId === courseId)
      .map((enrollment) => enrollment.learnerId);
    return users.filter((user) => learnerIds.includes(user.id));
  };

  const progressForEnrollment = (enrollment: Enrollment, course: Course) => {
    const totalLessons = course.modules.flatMap((module) => module.lessons).length;
    if (!totalLessons) return 0;
    return Math.round((enrollment.completedLessons.length / totalLessons) * 100);
  };

  const value = useMemo(
    () => ({
      courses,
      enrollments,
      announcements,
      certificates,
      submissions,
      createCourse,
      addModule,
      addLesson,
      enrollLearner,
      toggleLessonCompletion,
      issueCertificate,
      submitAssignment,
      recordAnnouncement,
      learnersForCourse,
      progressForEnrollment,
      activeRoleFilter,
      setActiveRoleFilter
    }),
    [
      courses,
      enrollments,
      announcements,
      certificates,
      submissions,
      activeRoleFilter,
      users
    ]
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export const useData = () => {
  const ctx = useContext(DataContext);
  if (!ctx) {
    throw new Error('useData must be used within a DataProvider');
  }
  return ctx;
};
