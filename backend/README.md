# EduFlow – Backend Persistence Layer

This directory contains the Python Flask + SQLAlchemy 2.x persistence layer, migrations, and automated test suite for **EduFlow – Assignment and Evaluation Management System**.

---

## 1. Prerequisites

- **Python**: 3.11+ (Tested on Python 3.14)
- **Database**: PostgreSQL 15+ (Production) / SQLite (Testing)
- **Package Manager**: `pip`

---

## 2. Installation

1. Clone or navigate to the repository:
   ```bash
   cd c:/Users/nagac/Downloads/eduflow
   ```

2. (Recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

---

## 3. Environment Variables Configuration

Copy the `.env.example` template into `.env`:
```bash
cp backend/.env.example backend/.env
```

### Environment Variables Reference

| Variable | Description | Default | Security Guidance |
| :--- | :--- | :--- | :--- |
| `FLASK_ENV` | Application environment (`development`, `testing`, `production`) | `development` | Use `production` in live deployments. |
| `FLASK_DEBUG` | Enable/disable Flask debug mode | `1` | Strictly `0` in production. |
| `SECRET_KEY` | Flask session and cryptographic secret key | Dev default string | Must be set to a cryptographically strong random key in `.env`. |
| `DB_USER` | PostgreSQL database username | `postgres` | Use least-privilege DB user. |
| `DB_PASSWORD` | PostgreSQL database password | None | Never hardcode or commit to version control. |
| `DB_HOST` | Database host | `localhost` | Production DB endpoint. |
| `DB_PORT` | Database port | `5432` | Standard PostgreSQL port. |
| `DB_NAME` | Database name | `eduflow_db` | Dedicated EduFlow database. |
| `DATABASE_URL` | Complete SQLAlchemy connection string | Auto-constructed from DB_* variables | Takes precedence if set. |
| `TEST_DATABASE_URL` | Database connection string for tests | `sqlite:///:memory:` | In-memory SQLite enables isolated test execution. |

> **SECURITY NOTE**: Never commit `.env` files. The `.gitignore` at the project root enforces this rule.

---

## 4. PostgreSQL Configuration & Database Creation

### Option A: Local PostgreSQL Service
1. Start the PostgreSQL service:
   ```powershell
   # Windows PowerShell
   Start-Service postgresql-x64-15
   ```
2. Create the application user and database via `psql`:
   ```sql
   CREATE USER eduflow_user WITH PASSWORD 'secure_password_here';
   CREATE DATABASE eduflow_db OWNER eduflow_user;
   GRANT ALL PRIVILEGES ON DATABASE eduflow_db TO eduflow_user;
   ```

### Option B: Docker Container
To spin up a local PostgreSQL 15 instance via Docker:
```bash
docker run --name eduflow-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=eduflow_db \
  -p 5432:5432 -d postgres:15-alpine
```

---

## 5. Database Migrations (Flask-Migrate & Alembic)

EduFlow uses Flask-Migrate (backed by Alembic) for schema versioning.

1. **Verify Migration Status**:
   ```powershell
   $env:PYTHONPATH="c:\Users\nagac\Downloads\eduflow"
   $env:FLASK_APP="backend.app:create_app('development')"
   python -m flask db current -d backend/migrations
   ```

2. **Apply Migrations to PostgreSQL**:
   ```powershell
   python -m flask db upgrade -d backend/migrations
   ```

3. **Generate a New Migration** (after model changes):
   ```powershell
   python -m flask db migrate -d backend/migrations -m "description_of_change"
   ```

4. **Rollback Migration**:
   ```powershell
   python -m flask db downgrade -d backend/migrations
   ```

---

## 6. Running Automated Tests

The automated test suite verifies all mandatory entities, unique constraints, foreign keys, rubric score validations, enrollment rules, submission versions, audit logs, timezone normalization, and the full REST API suite across all 10 modules.

Run the test suite with verbose output:
```powershell
$env:PYTHONPATH="c:\Users\nagac\Downloads\eduflow"
python -m pytest backend/tests -v
```

---

## 7. Phase 4: Flask REST API Documentation

EduFlow implements a comprehensive RESTful API built on Flask, SQLAlchemy 2.x, and Pydantic v2 domain validation. All responses adhere to standard HTTP status codes and uniform JSON payloads.

### API Architecture & Conventions

- **Base URL Prefix**: `/api`
- **Data Validation**: Enforced via Pydantic v2 schemas; invalid payloads return `422 Unprocessable Entity` with granular field-level diagnostics.
- **Transactional Integrity**: Critical operations (grading, resubmission approvals, appeals with grade modifications) execute inside atomic database transactions.
- **Audit Logging**: Sensitive mutations (grading, appeal adjustments) produce immutable `AuditLog` and `SubmissionStatusHistory` ledger entries.
- **Timezone Invariance**: All date/time fields are processed in UTC (`TIMESTAMPTZ`).

---

### Endpoint Catalog by Module

#### 1. Course APIs (`/api/courses`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/courses` | Create new course (validates `end_date > start_date`, unique code) | `201`, `409`, `422` |
| `GET` | `/api/courses` | List courses (filtering by `status`, `department`, `term`; pagination) | `200` |
| `GET` | `/api/courses/<id>` | View course details with total enrollment and assignment counts | `200`, `404` |
| `PATCH` | `/api/courses/<id>` | Update course metadata and lifecycle status | `200`, `404`, `422` |

#### 2. Learner APIs (`/api/learners`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/learners` | Register learner (unique student number & email validation) | `201`, `409`, `422` |
| `GET` | `/api/learners` | List learners (status filtering, full-text `search`, pagination) | `200` |
| `GET` | `/api/learners/<id>` | View learner profile with active course enrollments | `200`, `404` |
| `PATCH` | `/api/learners/<id>` | Update learner contact details and timezone | `200`, `404`, `409` |

#### 3. Enrollment APIs (`/api/enrollments`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/enrollments` | Enroll learner into course (enforces foreign keys & uniqueness) | `201`, `404`, `409` |
| `GET` | `/api/enrollments` | List enrollments (filterable by `course_id`, `learner_id`, `status`) | `200` |
| `GET` | `/api/enrollments/status` | Check enrollment verification (`?course_id=...&learner_id=...`) | `200`, `400` |
| `GET` | `/api/enrollments/<id>` | View enrollment details | `200`, `404` |
| `PATCH` | `/api/enrollments/<id>` | Update status (e.g., `active` -> `dropped` / `completed`) | `200`, `404`, `422` |

#### 4. Assignment & Rubric APIs (`/api/assignments`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/assignments` | Create assignment (with optional inline rubric & criteria) | `201`, `404`, `422` |
| `GET` | `/api/assignments` | List assignments (filterable by `course_id`, `status`, pagination) | `200` |
| `GET` | `/api/assignments/<id>` | View assignment details with versioned rubrics & criteria | `200`, `404` |
| `PATCH` | `/api/assignments/<id>` | Configure due dates, cutoff dates, late penalties, grace period | `200`, `404`, `422` |
| `POST` | `/api/assignments/<id>/publish` | Publish assignment (BR-04: enforces rubric criteria sum == max_score) | `200`, `404`, `422` |
| `POST` | `/api/assignments/<id>/rubrics` | Add new rubric version with itemized criteria | `201`, `404`, `422` |

#### 5. Submission APIs (`/api/submissions`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/submissions` | Submit assignment attempt (enforces active enrollment EX-01, cutoff EX-06, artifact checks EX-05, lateness BR-02) | `201`, `403`, `404`, `409`, `422` |
| `POST` | `/api/submissions/<id>/artifacts` | Upload artifact metadata (file size, SHA-256 checksum, MIME type) | `201`, `404`, `409`, `422` |
| `GET` | `/api/submissions` | List submissions (filter by `assignment_id`, `learner_id`, `status`) | `200` |
| `GET` | `/api/submissions/<id>` | View submission details, artifacts, grade, and lifecycle history | `200`, `404` |
| `GET` | `/api/submissions/<id>/history` | View immutable submission status transitions | `200`, `404` |
| `GET` | `/api/submissions/<id>/late-status` | Inspect submission lateness duration and penalty percentage | `200`, `404` |

#### 6. Grading APIs (`/api/grades`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/grades` | Grade submission using rubric criteria (enforces criterion max score bounds EX-02, applies late penalty exactly once EX-03, generates audit log) | `201`, `404`, `409`, `422` |
| `GET` | `/api/grades/<id>` | View grade breakdown with itemized criteria scores and deductions | `200`, `404` |
| `GET` | `/api/grades/submission/<id>` | View grade by submission ID | `200`, `404` |

#### 7. Feedback APIs (`/api/feedback`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/feedback` | Add instructor qualitative feedback (strengths, improvement areas) | `201`, `404`, `422` |
| `GET` | `/api/feedback` | List feedback (filter by `submission_id`, `grade_id`, `author_id`) | `200` |
| `GET` | `/api/feedback/<id>` | View specific feedback entry | `200`, `404` |

#### 8. Resubmission APIs (`/api/resubmissions`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/resubmissions` | Request resubmission (enforces cutoff EX-06, attempt limits EX-07) | `201`, `400`, `403`, `404`, `409` |
| `POST` | `/api/resubmissions/<id>/review` | Instructor decision (APPROVED creates attempt N+1; REJECTED updates status) | `200`, `404`, `422` |
| `GET` | `/api/resubmissions` | List resubmission requests | `200` |
| `GET` | `/api/resubmissions/<id>` | View resubmission record details | `200`, `404` |

#### 9. Appeal APIs (`/api/appeals`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/appeals` | Lodge grade appeal (enforces 7-day publication window EX-08, single active appeal) | `201`, `400`, `403`, `404`, `409` |
| `POST` | `/api/appeals/<id>/decision` | Adjudicate appeal (APPROVED atomically updates grade to `revised` and logs immutable `AuditLog` EX-04) | `200`, `404`, `422` |
| `GET` | `/api/appeals` | List appeals (filter by `status`, `learner_id`, `submission_id`) | `200` |
| `GET` | `/api/appeals/<id>` | View appeal details and decision history | `200`, `404` |

#### 10. Dashboard APIs (`/api/dashboard`)
| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/dashboard/stats` | Real-time aggregate platform metrics (total learners, courses, assignments, submissions, pending grading, late submissions, average grade, pending appeals) | `200` |

---

## 8. Full-Stack React Frontend Integration (Phase 6)

The React Single Page Application (SPA) in `frontend/` connects directly to this Flask API service.

### Full-Stack Architecture
* **Development Mode**:
  * Run backend: `python -m backend.app` (listening on `http://127.0.0.1:5000`)
  * Run frontend: `npm --prefix frontend run dev` (Vite dev server at `http://localhost:3000`, proxying `/api` requests to port `5000`)
* **Production Static Serving**:
  * Run build: `npm --prefix frontend run build` (compiles to `frontend/dist/`)
  * Flask automatically serves `index.html` and bundled assets from `frontend/dist/` when accessing `http://localhost:5000/`.
* **CORS & Multi-Host Configuration**:
  * Flask emits `Access-Control-Allow-Origin: *` and handles `OPTIONS` preflight requests.
  * In the frontend UI, clicking the gear icon allows dynamically changing the API Base URL (or setting `VITE_API_BASE_URL`).
* **Role-Based Authentication & Sessions**:
  * Switch between Learner, Instructor, and Administrator roles with persistent session state.
  * Auto-selects registered database learners to test active enrollments and submission histories.


