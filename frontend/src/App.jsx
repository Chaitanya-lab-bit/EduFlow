import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

// Views
import LearnerDashboard from './views/LearnerDashboard';
import InstructorDashboard from './views/InstructorDashboard';
import AdminDashboard from './views/AdminDashboard';
import CoursesView from './views/CoursesView';
import LearnersView from './views/LearnersView';
import AssignmentsView from './views/AssignmentsView';
import SubmissionsView from './views/SubmissionsView';
import GradingView from './views/GradingView';
import AppealsResubmissionsView from './views/AppealsResubmissionsView';

function AppContent() {
  const { role } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedAssignmentId, setSelectedAssignmentId] = useState(null);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState(null);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        if (role === 'instructor') {
          return (
            <InstructorDashboard
              setActiveTab={setActiveTab}
              setSelectedSubmissionId={setSelectedSubmissionId}
            />
          );
        }
        if (role === 'admin') {
          return <AdminDashboard setActiveTab={setActiveTab} />;
        }
        return (
          <LearnerDashboard
            setActiveTab={setActiveTab}
            setSelectedAssignmentId={setSelectedAssignmentId}
          />
        );

      case 'courses':
        return <CoursesView />;

      case 'learners':
        return <LearnersView />;

      case 'assignments':
        return <AssignmentsView />;

      case 'submissions':
        return <SubmissionsView selectedAssignmentId={selectedAssignmentId} />;

      case 'grading':
        return <GradingView selectedSubmissionId={selectedSubmissionId} />;

      case 'appeals':
        return <AppealsResubmissionsView />;

      default:
        return <LearnerDashboard setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-grow-1 container-fluid px-3 px-md-4 py-4">
        {renderContent()}
      </main>

      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
