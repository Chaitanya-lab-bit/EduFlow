# EduFlow Frontend — React & Bootstrap 5 SPA

Modern, responsive web client for the EduFlow Assignment and Evaluation Management System.

---

## 1. Overview & Architecture

The frontend is built with **React 18**, **Bootstrap 5.3**, and **Vite**, connecting directly to EduFlow's Python Flask REST API backend. It provides dedicated role-based portals for Learners, Instructors, and Administrators, with unified navigation, real-time rubric criteria computation, artifact checksum validation, and audit tracking.

### Core Technology Stack
* **Framework**: React 18+ (Functional Components & Hooks)
* **Styling & UI**: Bootstrap 5.3 + Bootstrap Icons + Custom CSS Design System
* **Build Tool**: Vite 6 (Lightning-fast HMR and optimized production bundling)
* **API Client**: Native `fetch` wrapper with unified error propagation, status code mapping, and query parameter handling
* **Backend Connection**: Configured via Vite reverse-proxy (`/api` &rarr; `http://127.0.0.1:5000`) and Flask static hosting (`/dist`)

---

## 2. Role-Based Dashboards & Workspaces

The platform features an interactive role switcher in the top navigation bar enabling immediate testing and transition between personas:

### 🎓 1. Learner Dashboard
* **Course Overview**: Summary of active enrolled courses with terms and schedules.
* **Upcoming Tasks**: Active assignments with live countdowns, due dates, grace periods, and maximum scores.
* **Submission Portal**: One-click submission initiation with artifact metadata and verified SHA-256 checksums.
* **Evaluation & Feedback**: Review attempt history, rubric scoring breakdowns, and instructor qualitative feedback.

### 👩‍🏫 2. Instructor Dashboard
* **Managed Courses**: Overview of active academic terms and enrolled cohorts.
* **Pending Grading Queue**: Prioritized list of submitted coursework awaiting evaluation.
* **Assignment Management**: Create assignments, configure multi-criteria grading rubrics, and publish tasks once point totals balance (BR-04).
* **Evaluation Workspace**: Criterion-by-criterion grading, automated late penalty deductions (BR-02 & BR-05), and qualitative feedback logging.

### 🛡️ 3. Administrator Dashboard
* **Platform Telemetry**: Direct aggregation from `GET /api/dashboard/stats`:
  * Total Learners
  * Total Courses
  * Total Assignments
  * Total Submissions
  * Pending Grading Count
  * Late Submissions
  * Average Grade Percentage
  * Pending Academic Appeals
* **Compliance & Governance**: Invariant monitoring for Universal UTC Timezone Normalization, Zero Silent Mutation, and Pydantic DTO Contract Validation.
* **Quick Administration**: Ingest learners, deploy courses, and monitor appeals.

---

## 3. Dedicated Modules & Views

1. **Course Catalog (`CoursesView.jsx`)**:
   * View courses with terms, schedules, timezones, and active statuses.
   * Add new courses with validated ISO dates and timezone mappings.
2. **Learner Directory (`LearnersView.jsx`)**:
   * Search registered students.
   * Register new learners with RFC-compliant email validation.
   * Enroll learners into institutional courses.
3. **Assignments & Rubrics (`AssignmentsView.jsx`)**:
   * List assignments with deadline schedules and grace periods.
   * Modal to author new assignments.
   * Dynamic Rubric Builder with real-time criteria point summation enforcing $ \sum \text{Points} = \text{Max Score} $.
   * Safe publication workflow (`POST /api/assignments/<id>/publish`).
4. **Submissions & Artifacts (`SubmissionsView.jsx`)**:
   * Ingestion form supporting multi-artifact attachments with checksums and byte sizes.
   * Lateness audit check (`GET /api/submissions/<id>/late-status`) displaying days late and penalty rates.
   * Attempt history tracking.
5. **Grading Workspace (`GradingView.jsx`)**:
   * Queue of pending student submissions.
   * Dynamic rubric scoring form with boundary validation ($0 \le \text{score} \le \text{max\_points}$).
   * Automatic calculation of Raw Score, Late Deduction %, and Final Score.
   * Qualitative instructor feedback with sentiment indicators (`positive`, `neutral`, `needs_improvement`).
6. **Appeals & Resubmissions (`AppealsResubmissionsView.jsx`)**:
   * Formal grade dispute filing with 7-day post-publication window validation (EX-08).
   * Formal committee adjudication with score adjustment and mandatory audit rationale (EX-04).
   * Resubmission authorization with automated attempt $N+1$ version incrementing.

---

## 4. Getting Started & Development

### Prerequisites
* Node.js v18+ (tested on Node.js v24)
* Python 3.10+ virtual environment with Flask backend running on port 5000

### Installation
```bash
cd frontend
npm install
```

### Development Mode (with Live Reload)
```bash
npm run dev
```
The application will launch at `http://localhost:3000`. API requests to `/api/*` are automatically forwarded to `http://127.0.0.1:5000`.

### Production Build
```bash
npm run build
```
Generates optimized static assets in `frontend/dist/`. The Flask backend automatically serves these files when accessing `http://localhost:5000/`.

