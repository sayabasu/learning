import React from 'react';
import { useAuth } from '../contexts/AuthContext';

interface TopBarProps {
  onCreateAnnouncement?: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ onCreateAnnouncement }) => {
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="brand">
        <img src="/logo.svg" alt="PulseLearn" />
        <span>PulseLearn LMS</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {onCreateAnnouncement && (
          <button className="btn-ghost" onClick={onCreateAnnouncement} type="button">
            + Announcement
          </button>
        )}
        {user && (
          <>
            <span style={{ color: '#475569', fontWeight: 500 }}>
              {user.name} · {user.role}
            </span>
            <button className="btn-primary" onClick={logout} type="button">
              Log out
            </button>
          </>
        )}
      </div>
    </header>
  );
};

export default TopBar;
