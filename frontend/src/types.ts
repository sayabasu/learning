export type Role = 'admin' | 'instructor' | 'learner';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}

export interface QuizQuestion {
  id: string;
  prompt: string;
  options: string[];
  answer: string;
}

export interface Lesson {
  id: string;
  title: string;
  contentType: 'video' | 'pdf' | 'text' | 'quiz' | 'assignment';
  description: string;
  resourceUrl?: string;
  quiz?: QuizQuestion[];
}

export interface Module {
  id: string;
  title: string;
  description: string;
  lessons: Lesson[];
}

export interface Course {
  id: string;
  title: string;
  category: string;
  description: string;
  instructorId: string;
  duration: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced';
  modules: Module[];
  tags: string[];
  createdAt: string;
}

export interface Enrollment {
  id: string;
  courseId: string;
  learnerId: string;
  enrolledAt: string;
  completedLessons: string[];
  completedAt?: string;
}

export interface Announcement {
  id: string;
  title: string;
  message: string;
  createdAt: string;
  authorId: string;
  target: Role | 'all';
}

export interface Certificate {
  id: string;
  courseId: string;
  learnerId: string;
  issuedAt: string;
}

export interface AssignmentSubmission {
  id: string;
  lessonId: string;
  learnerId: string;
  submittedAt: string;
  status: 'submitted' | 'graded';
  grade?: number;
  feedback?: string;
}
