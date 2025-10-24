import React, { useState } from 'react';
import AdminDashboard from './components/AdminDashboard';
import AnnouncementComposer from './components/AnnouncementComposer';
import InstructorDashboard from './components/InstructorDashboard';
import LearnerDashboard from './components/LearnerDashboard';
import LoginView from './components/LoginView';
import TopBar from './components/TopBar';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { DataProvider } from './contexts/DataContext';

const AppContent: React.FC = () => {
  const { user } = useAuth();
  const [showComposer, setShowComposer] = useState(false);

  if (!user) {
    return <LoginView />;
  }

  return (
    <div className="app-shell">
      <TopBar onCreateAnnouncement={user.role === 'admin' ? () => setShowComposer(true) : undefined} />
      <main>
        {user.role === 'admin' && (
          <AdminDashboard onComposeAnnouncement={() => setShowComposer(true)} />
        )}
        {user.role === 'instructor' && <InstructorDashboard />}
        {user.role === 'learner' && <LearnerDashboard />}
      </main>
      {showComposer && <AnnouncementComposer onClose={() => setShowComposer(false)} />}
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <DataProvider>
        <AppContent />
      </DataProvider>
    </AuthProvider>
  );
};

export default App;
