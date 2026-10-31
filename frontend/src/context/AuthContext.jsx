import React, { createContext, useContext, useState, useEffect } from 'react';
import { getApiBase, setApiBase, api } from '../api/client';

const AuthContext = createContext(null);

const DEFAULT_USERS = {
  learner: {
    id: 'LNR-2026-000001',
    name: 'Alex Johnson',
    email: 'alex.johnson@eduflow.edu',
    role: 'learner',
    timezone: 'UTC'
  },
  instructor: {
    id: 'INST-2026-0001',
    name: 'Dr. Evelyn Vance',
    email: 'e.vance@faculty.eduflow.edu',
    role: 'instructor',
    timezone: 'UTC'
  },
  admin: {
    id: 'ADMIN-2026-0001',
    name: 'EduFlow System Administrator',
    email: 'admin@ops.eduflow.edu',
    role: 'admin',
    timezone: 'UTC'
  }
};

export function AuthProvider({ children }) {
  const [role, setRoleState] = useState(() => {
    return localStorage.getItem('eduflow_role') || 'learner';
  });

  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('eduflow_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // fallback
      }
    }
    const initialRole = localStorage.getItem('eduflow_role') || 'learner';
    return DEFAULT_USERS[initialRole] || DEFAULT_USERS.learner;
  });

  const [apiBaseUrl, setApiBaseUrlState] = useState(getApiBase());
  const [availableLearners, setAvailableLearners] = useState([]);

  // Load available learners from API so learners can switch accounts
  useEffect(() => {
    api.getLearners({ per_page: 20 })
      .then(res => {
        if (res && res.items && res.items.length > 0) {
          setAvailableLearners(res.items);
        }
      })
      .catch(() => {
        // silently fallback to defaults if API not yet populated
      });
  }, [apiBaseUrl]);

  const switchRole = (newRole) => {
    setRoleState(newRole);
    localStorage.setItem('eduflow_role', newRole);

    let newUser = DEFAULT_USERS[newRole];
    // If switching to learner and we have registered learners from database, pick the first
    if (newRole === 'learner' && availableLearners.length > 0) {
      const dbLnr = availableLearners[0];
      newUser = {
        id: dbLnr.id,
        name: dbLnr.name,
        email: dbLnr.email,
        role: 'learner',
        timezone: dbLnr.timezone || 'UTC'
      };
    }

    setCurrentUser(newUser);
    localStorage.setItem('eduflow_user', JSON.stringify(newUser));
  };

  const loginAsUser = (userData) => {
    setCurrentUser(userData);
    setRoleState(userData.role || 'learner');
    localStorage.setItem('eduflow_role', userData.role || 'learner');
    localStorage.setItem('eduflow_user', JSON.stringify(userData));
  };

  const updateApiBaseUrl = (newUrl) => {
    setApiBase(newUrl);
    setApiBaseUrlState(getApiBase());
  };

  return (
    <AuthContext.Provider
      value={{
        role,
        currentUser,
        availableLearners,
        switchRole,
        loginAsUser,
        apiBaseUrl,
        updateApiBaseUrl,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

