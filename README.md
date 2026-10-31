# EduFlow — Assignment & Evaluation Management System

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Test Suite](https://img.shields.io/badge/pytest-145%20passed-success.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue.svg)]()
[![React](https://img.shields.io/badge/react-18.3.1-61dafb.svg)]()
[![Bootstrap](https://img.shields.io/badge/bootstrap-5.3.3-purple.svg)]()
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)]()
[![Deterministic Seed](https://img.shields.io/badge/seed-20261022-informational.svg)]()

**EduFlow** is an enterprise-grade academic coursework, submission, grading, resubmission, and appeals management platform designed for higher education and enterprise training environments. It features a transactional Python Flask REST API backed by SQLAlchemy 2.0 and PostgreSQL/SQLite, a responsive React 18 Single Page Application (SPA) with Bootstrap 5.3, and a high-throughput synthetic data generation engine seeded deterministically (`20261022`).

---

## 1. Executive Summary & Architectural Invariants

EduFlow enforces strict academic integrity and engineering invariants across all layers:

1. **Universal UTC Timezone Normalization**: All deadlines, grace periods, submission timestamps, and reviews are stored and evaluated strictly in UTC epoch timestamps. Client interfaces dynamically display localized representations using browser `Intl.DateTimeFormat`.
2. **Deterministic Alphanumeric Identity Hierarchy**:
   - Course: `CRS-2026-000001`
   - Learner: `LNR-2026-000001`
   - Enrollment: `ENR-2026-000001`
   - Assignment: `ASN-2026-000001`
   - Rubric: `RUB-ASN-2026-000001-01`
   - Criterion: `CRT-RUB-ASN-2026-000001-01-01`
   - Submission: `SUB-ASN-2026-000001-LNR-2026-000001-01`
   - Grade: `GRD-SUB-ASN-2026-000001-LNR-2026-000001-01`
   - Appeal: `APP-2026-000001`
3. **Zero Silent Mutation (Immutable Audit Trails)**: Historical grades, submission attempts, and appeal adjudications are never overwritten in-place without generating a linked record in `SubmissionStatusHistory` and the immutable `AuditLog` ledger (EX-04).
4. **Single Late Penalty Invariant (BR-02 & BR-05)**: Submissions submitted past the due date and grace period incur an automated late penalty deducted strictly once upon evaluation.
5. **Rubric Balance Gate (BR-04)**: Draft assignments cannot transition to `published` until active rubric criteria points sum exactly to `assignment.max_score`.
6. **Two-Tier Validation**: Pydantic v2 validates API DTOs in real-time with RFC-compliant checks, while vectorized Pandas engines benchmark enterprise data integrity.

---

## 2. Repository Layout

```
eduflow/
├── backend/                       # Python Flask Application & Persistence Tier
│   ├── app.py                     # Flask application factory, CORS, static serving & error handling
│   ├── config.py                  # Environment configurations (Dev, Test, Prod)
│   ├── extensions.py              # SQLAlchemy and Migrate instances
│   ├── schemas.py                 # Pydantic v2 request/response validation contracts
│   ├── utils.py                   # Custom API exceptions, serializers, and pagination helpers
│   ├── models/                    # SQLAlchemy 2.0 Mapped Models & Enumerations (15 entities)
│   ├── routes/                    # 10 Modular REST Blueprint routes + Health API
│   ├── tests/                     # 47 Database, REST API, and End-to-End Workflow tests
│   └── requirements.txt           # Python dependency manifest
├── data_generation/               # Vectorized Synthetic Data Generation Engine (Seed: 20261022)
│   ├── config.py                  # Generation parameters, distributions & volume targets
│   ├── main.py                    # Orchestrator & reproducible CLI pipeline
│   ├── generators/                # Independent domain entity generators (Beta, Poisson, Normal)
│   ├── validators/                # Vectorized relational integrity & calculation validators
│   ├── exports/full/              # Exported full datasets (CSV, JSON, SQL seed, Manifest)
│   └── ground_truth/              # Clean reference models and 4 labeled anomaly scenarios
├── docs/                          # Technical Specifications & Architecture Package
│   ├── architecture.md            # Topology, design patterns, component interactions & workflows
│   ├── database_schema.md         # Relational DDL, Mermaid ER diagram, indexes & constraints
│   ├── data_dictionary.md         # Comprehensive column-level specification for all 15 tables
│   ├── business_rules.md          # Business rules (BR-01..BR-05), exceptions (EX-01..EX-08) & formulas
│   └── data_generation.md         # Statistical distributions, mathematical models & validation
├── frontend/                      # React 18 + Bootstrap 5.3 Single Page Application (SPA)
│   ├── index.html                 # HTML5 container with Plus Jakarta Sans & JetBrains Mono typography
│   ├── vite.config.js             # Vite configuration with /api reverse-proxy
│   ├── package.json               # NPM packages & build scripts
│   ├── src/
│   │   ├── api/client.js          # Unified API client covering all 10 Flask REST modules
│   │   ├── context/AuthContext.js # Multi-persona session context (Learner, Instructor, Admin)
│   │   ├── components/            # Navbar, Footer, StatCard, StatusBadge, AlertBanner
│   │   └── views/                 # Dashboards, Courses, Learners, Assignments, Grading, Appeals
│   └── README.md                  # Frontend development guide
├── tests/                         # 98 Vectorized Data Generation & Reproducibility tests
├── pytest.ini                     # Pytest root configuration
├── .gitignore                     # Git ignore rules
└── README.md                      # Main project documentation (this file)
```

---

## 3. Quick Start & Execution Guide

### 3.1. Prerequisites
* **Python**: 3.11+ (Tested on Python 3.14)
* **Node.js**: v18+ (Tested on Node.js v24.21 & npm 11.19)
* **Database**: PostgreSQL 15+ (Production) or SQLite in-memory (Automated Testing)

### 3.2. Backend Setup
```bash
# 1. Create and activate a virtual environment
cd eduflow
python -m venv backend/venv

# Windows PowerShell:
.\backend\venv\Scripts\Activate.ps1
# Linux / macOS:
source backend/venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Launch Flask REST API server (port 5000)
python -m backend.app
```
The API gateway will be reachable at `http://127.0.0.1:5000/api`.

### 3.3. Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Run development server (with hot module replacement and proxy)
npm run dev
# The SPA will launch at http://localhost:3000

# 4. Or build production static assets
npm run build
# Assets compile to frontend/dist/ and are served automatically by Flask at http://localhost:5000/
```

### 3.4. Running Automated Tests
Run the complete, multi-tiered test suite across all 145 tests:
```bash
pytest -v
```

---

## 4. Synthetic Data Generation Engine

The data generation pipeline synthesizes enterprise-volume academic datasets seeded with fixed seed `20261022` using vectorized NumPy distributions (Beta, Poisson, Exponential, and Normal).

### 4.1. Generation Commands
```bash
# Run full synthetic dataset generation (Seed: 20261022)
python -m data_generation.main --scale full --seed 20261022 --export-all

# Run statistical diagnostics and validation suite
python -m data_generation.validators.data_validator
```

### 4.2. Target Volumes vs. Actual Record Counts

All target enterprise thresholds have been achieved and verified:

| Entity / Dataset | Target Volume | Actual Record Count | Export Formats | Primary Key Pattern |
| :--- | :---: | :---: | :---: | :--- |
| **Courses** | 100 | **100** | CSV, JSON, SQL | `CRS-2026-000001` |
| **Learners** | 10,000 | **10,000** | CSV, JSON, SQL | `LNR-2026-000001` |
| **Enrollments** | ~30,000 | **29,992** | CSV, JSON, SQL | `ENR-2026-000001` |
| **Assignments** | 1,000 | **1,000** | CSV, JSON, SQL | `ASN-2026-000001` |
| **Rubrics** | 1,000+ | **1,020** | CSV, JSON, SQL | `RUB-ASN-2026-000001-01` |
| **Rubric Criteria** | 5,000+ | **5,100** | CSV, JSON, SQL | `CRT-RUB-...-01-01` |
| **Submissions** | 30,000 | **33,000** | CSV, JSON, SQL | `SUB-ASN-...-LNR-...-01` |
| **Submission Artifacts** | — | **67,525** | CSV, JSON, SQL | `ART-SUB-...-01` |
| **Submission Status History** | — | **66,110** | CSV, JSON, SQL | `SSH-...` |
| **Grades** | — | **30,110** | CSV, JSON, SQL | `GRD-SUB-...-01` |
| **Grade Criterion Scores** | — | **150,550** | CSV, JSON, SQL | `GCS-...` |
| **Feedback** | — | **30,110** | CSV, JSON, SQL | `FB-...` |
| **Resubmissions** | — | **3,000** | CSV, JSON, SQL | `RSB-2026-000001` |
| **Appeals** | — | **1,356** | CSV, JSON, SQL | `APP-2026-000001` |
| **Audit Logs** | — | **546** | CSV, JSON, SQL | `AUD-...` |

### 4.3. SHA-256 Checksum Manifest (`data_generation/exports/full/manifest.json`)

| File | Size | SHA-256 Checksum |
| :--- | :---: | :--- |
| `assignment.csv` | 319.8 KB | `ae8851099399f9173ae03af35b41b4894acc140c28b5cc20ed19bf9268cdec77` |
| `course.csv` | 28.1 KB | `6b13d6ecc7427326ee1e18a53f9c8984469cb22931190562cc35ad26bba1b50d` |
| `learner.csv` | 1.55 MB | `6b330b2046e1178878cad19e757ba51c6305ff63c7a4fea1abc6434e104f9a67` |
| `enrollment.csv` | 4.05 MB | `48b5775874c63ac8d694354bf31b5d9806ee921b223fb424db9a5448788c9aef` |
| `rubric.csv` | 179.0 KB | `1d5605570e601e919d061755950324552153ee15df966d3c68f3487574204df2` |
| `rubric_criterion.csv` | 1.11 MB | `a7d891ea6e2ac8db2f1c8e9dcf11b8f58bb2d52071c2e1f49723e6def5f2cca2` |
| `submission.csv` | 8.32 MB | `1fc2dde4ca39ad65779a0a27b706a25a36b788730886ae331578d796e8db7b78` |
| `submission_artifact.csv` | 25.5 MB | `730e65b786ad9b4f85efaf091da4f39619d7925687441c4b7ac13feaa67647ee` |
| `submission_status_history.csv` | 11.5 MB | `3d875fcdaee020c8ca4d34e4dff685ea8813d54a6531e07b6198a16971bc0c40` |
| `grade.csv` | 6.81 MB | `efc456ad61f26617838ef11edfe580aaef841e6ee5fc6f6150cb484d53a92518` |
| `grade_criterion_score.csv` | 33.2 MB | `a8d018d3f4705f8b401fa6d430b0a9d1cefb7931d0fbd82fdbdad9493ca3a43c` |
| `feedback.csv` | 14.4 MB | `45d2f6b4cd064afb45bdeeaa9eabdeb42e38c1657a7e5a4ca14212bf7d527943` |
| `resubmission.csv` | 1.15 MB | `7e4b0bea5ea39852113a68f8de525f081434615b86712150ca989f997c49cd38` |
| `appeal.csv` | 743.0 KB | `657f5c58d780f64c576787010afad429a624153630185bba12d9dc1541eb5ffb` |
| `audit_log.csv` | 168.4 KB | `7e50e1f55087bff2912099a611e837cac51c820795c119f0d753d532303bbfa9` |
| **`seed.sql`** | **120.8 MB** | `bd12848ef13c74327b564bcad657307b00041fc1ad63b993798cd4a7da94b57b` |
| **`ground_truth/anomalies.csv`**| **3.9 KB** | `0d02b4de51b63e90cc39dcae4ca1349f62a6d6068baae62f12599800a66ae497` |

---

## 5. Ground Truth Labeled Anomalies

The synthetic generation suite maintains a separate, labeled ground-truth anomalous dataset in `data_generation/exports/full/ground_truth/anomalies.csv` to benchmark automated exception handlers:

| Anomaly ID | Scenario ID | Anomaly Name | Entity ID | Expected Error Code | HTTP Code | Enforced Mitigation Protocol |
| :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| `ANOM-2026-000001` | **EX-01** | `unenrolled_learner_submission` | `SUB-ASN-2026-000001-LNR-2026-000001-01` | `ERR_UNENROLLED_LEARNER` | `403` | Transaction aborted, submission rejected, foreign-key enrollment constraint asserted. |
| `ANOM-2026-000002` | **EX-02** | `grade_exceeding_rubric_max` | `GRD-CORRUPT-...` | `ERR_SCORE_EXCEEDS_MAX` | `422` | Pydantic validator and SQL `chk_grade_scores` check constraint intercept score > 100.0. |
| `ANOM-2026-000003` | **EX-03** | `duplicate_late_penalty` | `GRD-DUPPEN-...` | `ERR_DUPLICATE_LATE_PENALTY` | `422` | Grading engine guarantees idempotent single late deduction derived from immutable submission metadata (BR-05). |
| `ANOM-2026-000004` | **EX-04** | `appeal_grade_modification_without_audit` | `APP-2026-999999` | `ERR_MISSING_AUDIT_LOG` | `500` | Atomic Unit of Work rolls back grade modification if corresponding `AuditLog` entry is absent. |

---

## 6. REST API Endpoints Catalog

The backend exposes 10 comprehensive REST modules with Pydantic v2 validation, standardized JSON error envelopes, and HTTP status codes:

### 1. Course APIs (`/api/courses`)
* `POST /api/courses`: Create course (201, 400, 422)
* `GET /api/courses`: Paginated courses list with term and status filters (200)
* `GET /api/courses/<id>`: View course metadata and active enrollments count (200, 404)
* `PUT /api/courses/<id>`: Update syllabus, schedules, or timezone alignment (200, 404, 422)

### 2. Learner APIs (`/api/learners`)
* `POST /api/learners`: Register learner with RFC email verification (201, 409, 422)
* `GET /api/learners`: Search and filter learners by status and name (200)
* `GET /api/learners/<id>`: Detailed student profile (200, 404)
* `PUT /api/learners/<id>`: Update contact info or timezone (200, 404, 422)

### 3. Enrollment APIs (`/api/enrollments`)
* `POST /api/enrollments`: Enroll student in course; enforces uniqueness (201, 400, 409)
* `GET /api/enrollments`: Filter enrollments by course, learner, or status (200)
* `GET /api/enrollments/status`: Real-time enrollment verification check (200)

### 4. Assignment APIs (`/api/assignments`)
* `POST /api/assignments`: Author assignment as draft (201, 400, 422)
* `GET /api/assignments`: List assignments with course, date, and status filters (200)
* `GET /api/assignments/<id>`: Retrieve assignment details, grace period, and rubrics (200, 404)
* `PUT /api/assignments/<id>`: Update due dates, cutoffs, or late penalty rates (200, 404, 422)
* `POST /api/assignments/<id>/rubrics`: Configure multi-criteria rubrics (201, 404, 422)
* `POST /api/assignments/<id>/publish`: Publication gate enforcing BR-04 criteria sum == max score (200, 404, 422)

### 5. Submission APIs (`/api/submissions`)
* `POST /api/submissions`: Coursework submission with artifact metadata and lateness calculation (201, 400, 403, 422)
* `POST /api/submissions/<id>/artifacts`: Upload verified artifact metadata with SHA-256 (201, 404, 409)
* `GET /api/submissions`: List submissions with filtering (200)
* `GET /api/submissions/<id>`: View submission attempt and associated artifacts (200, 404)
* `GET /api/submissions/<id>/late-status`: Lateness audit endpoint (200, 404)
* `GET /api/submissions/<id>/history`: Audit trail of status transitions (200, 404)

### 6. Grading APIs (`/api/grades`)
* `POST /api/grades`: Rubric criteria scoring, automated late deduction, and atomic status transition (201, 400, 404, 422)
* `GET /api/grades/<id>`: Retrieve grade evaluation and criterion breakdowns (200, 404)
* `GET /api/grades/submission/<submission_id>`: Fetch grade by submission ID (200, 404)

### 7. Feedback APIs (`/api/feedback`)
* `POST /api/feedback`: Record instructor qualitative feedback with sentiment indicators (201, 404, 422)
* `GET /api/feedback`: Query feedback entries by grade or submission (200)
* `GET /api/feedback/<id>`: View specific feedback record (200, 404)

### 8. Resubmission APIs (`/api/resubmissions`)
* `POST /api/resubmissions`: Request resubmission within assignment attempt thresholds (201, 400, 403, 404)
* `POST /api/resubmissions/<id>/review`: Review resubmission; approval triggers attempt $N+1$ (200, 404, 422)
* `GET /api/resubmissions`: List resubmissions by status (200)

### 9. Appeal APIs (`/api/appeals`)
* `POST /api/appeals`: Lodge grade dispute within 7-day post-publication window (201, 400, 403, 404)
* `POST /api/appeals/<id>/decision`: Adjudicate appeal; approval updates grade and writes `AuditLog` (200, 404, 422)
* `GET /api/appeals`: Filter appeals by status or student (200)

### 10. Dashboard Telemetry APIs (`/api/dashboard`)
* `GET /api/dashboard/stats`: Aggregates all 8 platform metrics: Total Learners, Courses, Assignments, Submissions, Pending Grading, Late Submissions, Average Grade %, and Pending Appeals (200)

---

## 7. Automated Test Suite (145 Passing Tests)

The test suite validates the system across 4 distinct layers:

```bash
backend\venv\Scripts\pytest -v
```

1. **Synthetic Data Engine & Validation Tests (`tests/`) — 98 Tests**:
   - `test_data_generation.py`: Generation logic, deterministic seed validation (`20261022`), distribution models.
   - `test_data_validation.py`: Vectorized relational integrity, foreign key validity, score calculation benchmarks.
   - `test_reproducibility.py`: Exact bit-for-bit repeatability across independent runs with identical seeds.
2. **Database Persistence Layer Tests (`backend/tests/test_database_layer.py`) — 9 Tests**:
   - SQLAlchemy 2.0 mapped models, check constraints, cascade deletions, immutability listeners.
3. **REST API Endpoint Tests (`backend/tests/test_api_endpoints.py`) — 30 Tests**:
   - Unit tests covering all 10 Blueprint modules, Pydantic input validation, HTTP error codes, and CORS headers.
4. **End-to-End Workflow Tests (`backend/tests/test_end_to_end_workflows.py`) — 8 Tests**:
   - Full lifecycle simulations from course creation, rubric balancing, submission, and grading to feedback, resubmission, and appeal adjudication.

---

## 8. GitHub Public Repository Preparation

To publish this repository to GitHub:

```bash
# 1. Initialize git repository (if not initialized)
git init

# 2. Verify .gitignore ignores virtual environments, node_modules, and cache
git status

# 3. Stage source files, documentation, and manifest
git add backend/ data_generation/ docs/ frontend/ tests/ .gitignore pytest.ini README.md

# 4. Create initial release commit
git commit -m "feat: complete EduFlow platform (Phases 1-8 release)"

# 5. Link remote repository and push
git remote add origin https://github.com/<your-username>/eduflow.git
git branch -M main
git push -u origin main
```

