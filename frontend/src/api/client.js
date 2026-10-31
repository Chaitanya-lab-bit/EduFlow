/**
 * Dynamic API Base URL configuration
 */
export const getApiBase = () => {
  return localStorage.getItem('eduflow_api_base') || import.meta.env.VITE_API_BASE_URL || '/api';
};

export const setApiBase = (url) => {
  if (url && url.trim()) {
    localStorage.setItem('eduflow_api_base', url.trim().replace(/\/$/, ''));
  } else {
    localStorage.removeItem('eduflow_api_base');
  }
};

/**
 * Universal JSON fetch helper with unified error extraction
 */
async function apiRequest(endpoint, options = {}) {
  const base = getApiBase();
  const url = `${base}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    const contentType = res.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const data = isJson ? await res.json() : await res.text();

    if (!res.ok) {
      let errorMessage = 'Request failed';
      let errorCode = null;
      let details = null;

      if (typeof data === 'object' && data !== null) {
        if (data.error) errorMessage = data.error;
        if (data.error_code) errorCode = data.error_code;
        if (data.details) details = data.details;

        if (details && !errorMessage.includes(':')) {
          if (Array.isArray(details)) {
            const detailMsgs = details.map(d => (d && d.msg) || JSON.stringify(d)).join('; ');
            if (detailMsgs) errorMessage += `: ${detailMsgs}`;
          } else if (typeof details === 'string') {
            errorMessage += ` (${details})`;
          }
        }
      } else if (typeof data === 'string') {
        errorMessage = data;
      }

      const err = new Error(errorMessage);
      err.status = res.status;
      err.error_code = errorCode;
      err.details = details;
      err.data = data;
      throw err;
    }

    return data;
  } catch (error) {
    if (!error.status) {
      // Network failure or CORS block
      console.error(`Network Error [${options.method || 'GET'} ${url}]:`, error);
      const netErr = new Error(`Cannot reach API at ${url}. Check server connectivity.`);
      netErr.status = 0;
      netErr.error_code = 'ERR_NETWORK';
      throw netErr;
    }
    throw error;
  }
}

export const api = {
  // Health API
  checkHealth: () => apiRequest('/health'),

  // Course APIs
  getCourses: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/courses${q ? '?' + q : ''}`);
  },
  getCourse: (id) => apiRequest(`/courses/${id}`),
  createCourse: (data) => apiRequest('/courses', { method: 'POST', body: JSON.stringify(data) }),
  updateCourse: (id, data) => apiRequest(`/courses/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Learner APIs
  getLearners: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/learners${q ? '?' + q : ''}`);
  },
  getLearner: (id) => apiRequest(`/learners/${id}`),
  registerLearner: (data) => apiRequest('/learners', { method: 'POST', body: JSON.stringify(data) }),
  updateLearner: (id, data) => apiRequest(`/learners/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Enrollment APIs
  enrollLearner: (data) => apiRequest('/enrollments', { method: 'POST', body: JSON.stringify(data) }),
  getEnrollments: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/enrollments${q ? '?' + q : ''}`);
  },
  checkEnrollmentStatus: (learnerId, courseId) => 
    apiRequest(`/enrollments/status?learner_id=${encodeURIComponent(learnerId)}&course_id=${encodeURIComponent(courseId)}`),

  // Assignment APIs
  getAssignments: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/assignments${q ? '?' + q : ''}`);
  },
  getAssignment: (id) => apiRequest(`/assignments/${id}`),
  createAssignment: (data) => apiRequest('/assignments', { method: 'POST', body: JSON.stringify(data) }),
  updateAssignment: (id, data) => apiRequest(`/assignments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  configureRubrics: (assignmentId, rubrics) => 
    apiRequest(`/assignments/${assignmentId}/rubrics`, { method: 'POST', body: JSON.stringify({ rubrics }) }),
  publishAssignment: (id) => apiRequest(`/assignments/${id}/publish`, { method: 'POST' }),

  // Submission APIs
  submitAssignment: (data) => apiRequest('/submissions', { method: 'POST', body: JSON.stringify(data) }),
  uploadArtifactMetadata: (submissionId, data) => 
    apiRequest(`/submissions/${submissionId}/artifacts`, { method: 'POST', body: JSON.stringify(data) }),
  getSubmissionHistory: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/submissions/history${q ? '?' + q : ''}`);
  },
  checkLateStatus: (submissionId) => apiRequest(`/submissions/${submissionId}/late-status`),

  // Grading APIs
  gradeSubmission: (data) => apiRequest('/grades', { method: 'POST', body: JSON.stringify(data) }),
  getGrade: (id) => apiRequest(`/grades/${id}`),
  getGradeBySubmission: (submissionId) => apiRequest(`/grades/submission/${submissionId}`),

  // Feedback APIs
  addFeedback: (data) => apiRequest('/feedback', { method: 'POST', body: JSON.stringify(data) }),
  getFeedback: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/feedback${q ? '?' + q : ''}`);
  },

  // Resubmission APIs
  requestResubmission: (data) => apiRequest('/resubmissions', { method: 'POST', body: JSON.stringify(data) }),
  getResubmissions: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/resubmissions${q ? '?' + q : ''}`);
  },
  reviewResubmission: (id, data) => 
    apiRequest(`/resubmissions/${id}/review`, { method: 'POST', body: JSON.stringify(data) }),

  // Appeal APIs
  submitAppeal: (data) => apiRequest('/appeals', { method: 'POST', body: JSON.stringify(data) }),
  getAppeals: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/appeals${q ? '?' + q : ''}`);
  },
  decideAppeal: (id, data) => 
    apiRequest(`/appeals/${id}/decision`, { method: 'POST', body: JSON.stringify(data) }),

  // Dashboard APIs
  getDashboardStats: () => apiRequest('/dashboard/stats'),
};
