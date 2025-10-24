import React, { createContext, useContext, useMemo, useState } from 'react';
import type { Role, User } from '../types';
import { generateId } from '../utils';

interface AuthContextValue {
  user: User | null;
  users: User[];
  login: (email: string, role: Role) => void;
  logout: () => void;
  register: (name: string, email: string, role: Role) => void;
}

const initialUsers: User[] = [
  { id: 'u-admin', name: 'Alicia Rhodes', email: 'admin@pulselearn.com', role: 'admin' },
  { id: 'u-mentor', name: 'Jonah Patel', email: 'mentor@pulselearn.com', role: 'instructor' },
  { id: 'u-learner', name: 'Jordan Chen', email: 'jordan@pulselearn.com', role: 'learner' }
];

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>(initialUsers);

  const login = (email: string, role: Role) => {
    const match = users.find((u) => u.email === email && u.role === role);
    if (match) {
      setUser(match);
      return;
    }

    const generated: User = {
      id: generateId(),
      name: email.split('@')[0] ?? 'Guest',
      email,
      role
    };

    setUsers((prev) => [...prev, generated]);
    setUser(generated);
  };

  const register = (name: string, email: string, role: Role) => {
    const exists = users.some((u) => u.email === email);
    if (exists) {
      return login(email, role);
    }

    const newUser: User = {
      id: generateId(),
      name,
      email,
      role
    };

    setUsers((prev) => [...prev, newUser]);
    setUser(newUser);
  };

  const logout = () => setUser(null);

  const value = useMemo(() => ({ user, users, login, logout, register }), [user, users]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};
