import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import type { Role } from '../types';

const roles: { label: string; value: Role }[] = [
  { label: 'Admin', value: 'admin' },
  { label: 'Instructor', value: 'instructor' },
  { label: 'Learner', value: 'learner' }
];

const LoginView: React.FC = () => {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [role, setRole] = useState<Role>('admin');
  const [email, setEmail] = useState('admin@pulselearn.com');
  const [name, setName] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (mode === 'login') {
      login(email, role);
    } else {
      register(name || email.split('@')[0], email, role);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        background: 'linear-gradient(135deg, #1d4ed8, #0f172a)'
      }}
    >
      <div className="card" style={{ width: 'min(420px, 90vw)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, color: '#0f172a' }}>PulseLearn LMS</h2>
          <div className="badge">beta</div>
        </div>
        <p style={{ color: '#475569', marginTop: '0.5rem' }}>
          Craft, deliver, and celebrate learning moments. Choose your role to get started.
        </p>

        <div className="tab-bar" style={{ marginTop: '1.25rem' }}>
          <button
            className={mode === 'login' ? 'active' : ''}
            onClick={() => setMode('login')}
            type="button"
          >
            Sign in
          </button>
          <button
            className={mode === 'register' ? 'active' : ''}
            onClick={() => setMode('register')}
            type="button"
          >
            Create account
          </button>
        </div>

        <form className="form" style={{ marginTop: '1.5rem' }} onSubmit={handleSubmit}>
          {mode === 'register' && (
            <label>
              Full name
              <input
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Amina Torres"
              />
            </label>
          )}

          <label>
            Email address
            <input
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@pulselearn.com"
            />
          </label>

          <label>
            Role
            <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
              {roles.map((roleOption) => (
                <option key={roleOption.value} value={roleOption.value}>
                  {roleOption.label}
                </option>
              ))}
            </select>
          </label>

          <button className="btn-primary" type="submit">
            {mode === 'login' ? 'Enter workspace' : 'Create and continue'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginView;
