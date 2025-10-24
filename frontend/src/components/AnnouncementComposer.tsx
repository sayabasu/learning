import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useData } from '../contexts/DataContext';
import type { Role } from '../types';

interface AnnouncementComposerProps {
  onClose: () => void;
}

const AnnouncementComposer: React.FC<AnnouncementComposerProps> = ({ onClose }) => {
  const { user } = useAuth();
  const { recordAnnouncement } = useData();
  const [title, setTitle] = useState('Campus update');
  const [message, setMessage] = useState('We just unlocked new maker labs inside PulseLearn. Explore the catalogue!');
  const [target, setTarget] = useState<Role | 'all'>('all');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    recordAnnouncement({
      title,
      message,
      target,
      authorId: user?.id ?? 'system'
    });
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 23, 42, 0.65)',
        display: 'grid',
        placeItems: 'center',
        zIndex: 50,
        padding: '1rem'
      }}
    >
      <form className="card form" style={{ width: 'min(480px, 95vw)' }} onSubmit={handleSubmit}>
        <h3 style={{ marginTop: 0 }}>Share announcement</h3>
        <label>
          Headline
          <input value={title} onChange={(event) => setTitle(event.target.value)} required />
        </label>
        <label>
          Message
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="What would you like everyone to know?"
          />
        </label>
        <label>
          Audience
          <select value={target} onChange={(event) => setTarget(event.target.value as Role | 'all')}>
            <option value="all">Everyone</option>
            <option value="admin">Admins</option>
            <option value="instructor">Instructors</option>
            <option value="learner">Learners</option>
          </select>
        </label>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
          <button className="btn-ghost" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" type="submit">
            Publish
          </button>
        </div>
      </form>
    </div>
  );
};

export default AnnouncementComposer;
