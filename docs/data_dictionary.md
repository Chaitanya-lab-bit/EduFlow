# EduFlow – Comprehensive Data Dictionary

## 1. Introduction

This document provides the definitive data dictionary for the **EduFlow** persistence layer. It defines all tables, columns, data types, constraints, default values, business rules, and sample values conforming strictly to the project's deterministic naming conventions.

---

## 2. Enumerated Domain Types (Enums)

### 2.1. `course_status`
- `draft`: Course is being constructed; not visible to learners.
- `active`: Course is actively running; enrollments and assignments are active.
- `archived`: Course has concluded; read-only access for historical records.

### 2.2. `enrollment_status`
- `active`: Learner is formally enrolled and eligible to submit assignments.
- `dropped`: Learner withdrew; cannot submit new work.
- `completed`: Learner finished the course.
- `suspended`: Administrative hold; submissions blocked pending review.

### 2.3. `assignment_status`
- `draft`: Assignment is under development; rubrics being configured.
- `published`: Assignment is open for submissions.
- `closed`: Assignment deadline passed (cutoff reached); no new initial submissions accepted.
- `archived`: Final grades locked; assignment stored for archival.

### 2.4. `submission_status`
- `draft`: Artifacts uploaded but not officially submitted.
- `submitted`: Formally submitted; awaiting grading.
- `under_review`: Grader or automated engine currently scoring.
- `graded`: Grade and feedback published to learner.
- `resubmitted`: Superseded by a subsequent attempt.
- `appealed`: Under formal appeal review.

### 2.5. `artifact_type`
- `code_repository`: Git URL or zipped repository archive.
- `report_pdf`: PDF technical report or paper.
- `dataset_csv`: Tabular CSV/Parquet data asset.
- `video_presentation`: Recorded video demo / MP4 link.
- `supplementary_zip`: Miscellaneous supporting code/files.

### 2.6. `grade_status`
- `provisional`: Scored by grader, awaiting moderation/release.
- `published`: Officially released to learner.
- `revised`: Modified via formal appeal or regrade procedure.
- `disputed`: Flagged during an active appeal.

### 2.7. `feedback_visibility`
- `learner_visible`: Accessible by learner upon grade publication.
- `internal_staff_only`: Confidential notes among teaching staff and auditors.

### 2.8. `resubmission_status`
- `requested`: Learner formally requested resubmission permission.
- `approved`: Staff permitted a second attempt.
- `rejected`: Resubmission request denied.
- `submitted`: New attempt submitted and entered grading queue.

### 2.9. `appeal_status`
- `submitted`: Appeal registered by learner.
- `under_review`: Assigned to academic reviewer or committee.
- `approved`: Grade adjusted in learner's favor.
- `rejected`: Original grade upheld.
- `withdrawn`: Learner cancelled appeal.

### 2.10. `appeal_reason_category`
- `calculation_error`: Mathematical error in rubric sum or penalty deduction.
- `rubric_misinterpretation`: Grader misapplied criteria definitions.
- `missing_artifact_reconsideration`: Verification of erroneously flagged missing file.
- `extenuating_circumstances`: Medical or institutional exemption granted.

### 2.11. `audit_action_type`
- `INSERT`: New entity created.
- `UPDATE`: Entity attribute modified.
- `DELETE`: Entity soft-deleted or removed.
- `STATUS_CHANGE`: Workflow status transition.
- `GRADE_OVERRIDE`: Manual score alteration.
- `APPEAL_DECISION`: Committee resolution applied to grade.
- `ARTIFACT_VERIFICATION`: Automated or manual file integrity check.

---

## 3. Entity Data Dictionaries

### 3.1. `course`
Stores foundational academic course offerings.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `course_id` | `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Deterministic identifier format: `CRS-YYYY-NNNNNN`. | `CRS-2026-000001` |
| `code` | `VARCHAR(32)` / `String(32)` | UNIQUE, NOT NULL | None | Unique departmental course code. | `CS-504` |
| `title` | `VARCHAR(255)` / `String(255)` | NOT NULL | None | Full title of the course. | `Distributed Data Systems` |
| `description` | `TEXT` / `Text` | NULLABLE | None | Detailed syllabus and course overview. | `Advanced concepts in data modeling...` |
| `department` | `VARCHAR(100)` / `String(100)` | NOT NULL | None | Academic department administering course. | `Computer Science` |
| `term` | `VARCHAR(32)` / `String(32)` | NOT NULL | None | Academic term and calendar year. | `Fall 2026` |
| `timezone` | `VARCHAR(64)` / `String(64)` | NOT NULL | `'UTC'` | Canonical IANA timezone for course deadlines. | `America/New_York` |
| `status` | `course_status` / `Enum` | NOT NULL | `'draft'` | Current administrative lifecycle stage. | `active` |
| `start_date` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | None | Course term commencement date. | `2026-09-01 00:00:00+00` |
| `end_date` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | None | Course term conclusion date (`end_date > start_date`). | `2026-12-20 23:59:59+00` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | System creation audit timestamp in UTC. | `2026-08-15 10:00:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last modification audit timestamp in UTC. | `2026-08-20 14:30:00+00` |

---

### 3.2. `learner`
Stores enrolled students and academic participants.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `learner_id` | `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Deterministic identifier format: `LNR-YYYY-NNNNNN`. | `LNR-2026-000001` |
| `student_number`| `VARCHAR(64)` / `String(64)` | UNIQUE, NOT NULL | None | Institutional matriculation number. | `STU-984321` |
| `first_name` | `VARCHAR(100)` / `String(100)` | NOT NULL | None | Legal first name. | `Alex` |
| `last_name` | `VARCHAR(100)` / `String(100)` | NOT NULL | None | Legal surname. | `Chen` |
| `email` | `VARCHAR(255)` / `String(255)` | UNIQUE, NOT NULL | None | Institutional academic email address. | `alex.chen@university.edu` |
| `timezone` | `VARCHAR(64)` / `String(64)` | NOT NULL | `'UTC'` | Preferred local learner timezone. | `America/Los_Angeles` |
| `status` | `enrollment_status` / `Enum` | NOT NULL | `'active'` | Standing of the student profile. | `active` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Registration timestamp. | `2026-08-25 09:12:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last profile update timestamp. | `2026-08-25 09:12:00+00` |

---

### 3.3. `enrollment`
Associative entity binding Learners to Courses with active standing verification.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `enrollment_id` | `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Deterministic identifier format: `ENR-YYYY-NNNNNN`. | `ENR-2026-000001` |
| `course_id` | `VARCHAR(32)` / `String(32)` | FK (`course.course_id`), NOT NULL | None | Target course offering. | `CRS-2026-000001` |
| `learner_id` | `VARCHAR(32)` / `String(32)` | FK (`learner.learner_id`), NOT NULL | None | Enrolled student. | `LNR-2026-000001` |
| `status` | `enrollment_status` / `Enum` | NOT NULL | `'active'` | Current participation status. Only `active` may submit. | `active` |
| `enrolled_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Date enrollment was formalized. | `2026-08-28 11:00:00+00` |
| `dropped_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NULLABLE | None | Date student withdrew from course if applicable. | `NULL` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Record creation audit timestamp. | `2026-08-28 11:00:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last status update audit timestamp. | `2026-08-28 11:00:00+00` |

*Table Constraint*: `CONSTRAINT uq_course_learner UNIQUE (course_id, learner_id)`

---

### 3.4. `assignment`
Defines deliverable specifications, scoring rules, deadlines, and artifact policies.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `assignment_id` | `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Mandatory exact format: `ASN-YYYY-NNNNNN`. | `ASN-2026-000001` |
| `course_id` | `VARCHAR(32)` / `String(32)` | FK (`course.course_id`), NOT NULL | None | Owning course identifier. | `CRS-2026-000001` |
| `title` | `VARCHAR(255)` / `String(255)` | NOT NULL | None | Assignment deliverable title. | `Pipeline ETL Architecture` |
| `description` | `TEXT` / `Text` | NULLABLE | None | Detailed assignment requirements and prompt. | `Build a streaming ETL pipeline using...` |
| `max_score` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `> 0` | `100.00` | Maximum possible raw score obtainable. | `100.00` |
| `due_date` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | None | Official deadline for full credit (UTC). | `2026-10-15 23:59:59+00` |
| `cutoff_date` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL, `>= due_date` | None | Hard deadline after which no submissions permitted. | `2026-10-18 23:59:59+00` |
| `late_penalty_per_day`| `NUMERIC(4, 2)` / `Numeric(4,2)`| NOT NULL, `0..100` | `5.00` | Percentage penalty applied per 24 hours late. | `5.00` |
| `max_late_days` | `INTEGER` / `Integer` | NOT NULL, `>= 0` | `3` | Maximum days after due date before automatic zero. | `3` |
| `grace_period_minutes`| `INTEGER` / `Integer` | NOT NULL, `>= 0` | `15` | Window post-deadline where penalty is waived. | `15` |
| `max_resubmissions` | `INTEGER` / `Integer` | NOT NULL, `>= 0` | `1` | Total allowable re-attempts after attempt 1. | `1` |
| `required_artifact_types` | `JSONB` / `JSONB` | NOT NULL | `'["report_pdf"]'` | Array of mandatory artifact types required for submission. | `["code_repository", "report_pdf"]` |
| `status` | `assignment_status` / `Enum` | NOT NULL | `'draft'` | Current lifecycle stage of assignment. | `published` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Ingestion timestamp. | `2026-09-01 12:00:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last configuration edit timestamp. | `2026-09-02 15:30:00+00` |

---

### 3.5. `rubric`
Defines the scoring schema for an assignment.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rubric_id` | `VARCHAR(64)` / `String(64)` | PK, NOT NULL | None | Mandatory exact format: `RUB-<assignment-id>-NN`. | `RUB-ASN-2026-000001-01` |
| `assignment_id` | `VARCHAR(32)` / `String(32)` | FK (`assignment.assignment_id`), NOT NULL | None | Target assignment. | `ASN-2026-000001` |
| `title` | `VARCHAR(255)` / `String(255)` | NOT NULL | None | Name of grading rubric. | `Standard Systems Rubric v1` |
| `description` | `TEXT` / `Text` | NULLABLE | None | Rubric guidance notes for evaluators. | `Evaluate code quality, schema...` |
| `total_points` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `> 0` | `100.00` | Sum of all criteria points; must match `assignment.max_score`. | `100.00` |
| `version` | `INTEGER` / `Integer` | NOT NULL | `1` | Sequential version index for rubric revisions. | `1` |
| `is_active` | `BOOLEAN` / `Boolean` | NOT NULL | `TRUE` | Whether this version is active for evaluation. | `TRUE` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Rubric creation timestamp. | `2026-09-02 16:00:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last rubric edit timestamp. | `2026-09-02 16:00:00+00` |

*Table Constraint*: `CONSTRAINT uq_rubric_assignment_version UNIQUE (assignment_id, version)`

---

### 3.6. `rubric_criterion`
Defines individual evaluation criteria within a rubric.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `criterion_id` | `VARCHAR(96)` / `String(96)` | PK, NOT NULL | None | Format: `CRT-<rubric-id>-NN`. | `CRT-RUB-ASN-2026-000001-01-01` |
| `rubric_id` | `VARCHAR(64)` / `String(64)` | FK (`rubric.rubric_id`), NOT NULL | None | Parent rubric ID. Cascades on delete. | `RUB-ASN-2026-000001-01` |
| `criterion_name`| `VARCHAR(255)` / `String(255)` | NOT NULL | None | Specific skill or deliverable being graded. | `Architectural Modularity` |
| `description` | `TEXT` / `Text` | NULLABLE | None | Performance benchmarks and scoring tiers. | `Full points for clear separation of concerns.` |
| `max_points` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `> 0` | None | Maximum points achievable on this criterion. | `25.00` |
| `weight` | `NUMERIC(4, 2)` / `Numeric(4,2)` | NOT NULL, `> 0` | `1.00` | Relative weighting factor (normalized). | `1.00` |
| `display_order` | `INTEGER` / `Integer` | NOT NULL | `1` | Sort order for display in grading UI. | `1` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Creation timestamp. | `2026-09-02 16:15:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Modification timestamp. | `2026-09-02 16:15:00+00` |

---

### 3.7. `submission`
Captures an attempt by a student to deliver an assignment.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `submission_id` | `VARCHAR(96)` / `String(96)` | PK, NOT NULL | None | Mandatory exact format: `SUB-<assignment-id>-<learner-id>-NN`. | `SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `assignment_id` | `VARCHAR(32)` / `String(32)` | FK (`assignment.assignment_id`), NOT NULL | None | Target assignment. | `ASN-2026-000001` |
| `learner_id` | `VARCHAR(32)` / `String(32)` | FK (`learner.learner_id`), NOT NULL | None | Submitting student. | `LNR-2026-000001` |
| `enrollment_id` | `VARCHAR(32)` / `String(32)` | FK (`enrollment.enrollment_id`), NOT NULL | None | Active enrollment link. | `ENR-2026-000001` |
| `attempt_number`| `INTEGER` / `Integer` | NOT NULL, `>= 1` | `1` | Attempt index (1 for initial, 2+ for resubmission). | `1` |
| `submitted_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Submission timestamp recorded in UTC. | `2026-10-15 22:30:00+00` |
| `status` | `submission_status` / `Enum` | NOT NULL | `'submitted'` | Processing state in evaluation pipeline. | `graded` |
| `is_late` | `BOOLEAN` / `Boolean` | NOT NULL | `FALSE` | Flag set if `submitted_at > due_date + grace_period`. | `FALSE` |
| `late_duration_seconds`| `INTEGER` / `Integer` | NOT NULL, `>= 0` | `0` | Calculated seconds submitted after due date. | `0` |
| `late_penalty_percentage`| `NUMERIC(5, 2)` / `Numeric(5,2)`| NOT NULL, `0..100` | `0.00` | Penalty % deduced based on assignment late policy. | `0.00` |
| `raw_score` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NULLABLE, `>= 0` | None | Unpenalized sum of rubric criteria scores. | `92.00` |
| `final_score` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NULLABLE, `>= 0` | None | Net score after penalty and bonus adjustments. | `92.00` |
| `learner_notes` | `TEXT` / `Text` | NULLABLE | None | Optional note submitted by the learner. | `Repository includes unit test suite.` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Initial record timestamp. | `2026-10-15 22:28:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last status or score update timestamp. | `2026-10-17 14:00:00+00` |

*Table Constraint*: `CONSTRAINT uq_submission_attempt UNIQUE (assignment_id, learner_id, attempt_number)`

---

### 3.8. `submission_artifact`
Digital assets attached to a submission attempt.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `artifact_id` | `VARCHAR(128)` / `String(128)`| PK, NOT NULL | None | Format: `ART-<submission-id>-NN`. | `ART-SUB-ASN-2026-000001-LNR-2026-000001-01-01` |
| `submission_id` | `VARCHAR(96)` / `String(96)` | FK (`submission.submission_id`), NOT NULL | None | Owning submission attempt. Cascades on delete. | `SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `artifact_type` | `artifact_type` / `Enum` | NOT NULL | None | Type of artifact delivered. | `report_pdf` |
| `file_name` | `VARCHAR(255)` / `String(255)` | NOT NULL | None | Original upload filename. | `alex_chen_etl_report.pdf` |
| `file_size_bytes`| `BIGINT` / `BigInteger` | NOT NULL, `> 0` | None | File size; 0-byte files strictly rejected. | `2458900` |
| `mime_type` | `VARCHAR(128)` / `String(128)` | NOT NULL | None | Standard Internet Media Type. | `application/pdf` |
| `storage_uri` | `VARCHAR(512)` / `String(512)` | NOT NULL | None | S3 / MinIO / Local secure storage URI. | `s3://eduflow-artifacts/2026/asn-1/chen_report.pdf` |
| `checksum_sha256`| `VARCHAR(64)` / `String(64)` | NOT NULL | None | SHA-256 digest ensuring artifact immutability. | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `is_verified` | `BOOLEAN` / `Boolean` | NOT NULL | `TRUE` | Checksum and MIME integrity verified flag. | `TRUE` |
| `uploaded_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Ingestion timestamp. | `2026-10-15 22:29:15+00` |

*Table Constraint*: `CONSTRAINT uq_submission_artifact_type UNIQUE (submission_id, artifact_type)`

---

### 3.9. `grade`
Formal academic assessment result linked 1:1 to a submission.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `grade_id` | `VARCHAR(112)` / `String(112)`| PK, NOT NULL | None | Mandatory exact format: `GRD-<submission-id>`. | `GRD-SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `submission_id` | `VARCHAR(96)` / `String(96)` | FK (`submission.submission_id`), NOT NULL, UNIQUE | None | Exactly one grade record per submission attempt. | `SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `graded_by` | `VARCHAR(64)` / `String(64)` | NOT NULL | None | Identifier of evaluator (Instructor/TA). | `USR-INST-0042` |
| `raw_score` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `>= 0` | None | Sum of individual rubric criteria scores. | `95.00` |
| `late_penalty_applied`| `NUMERIC(5, 2)` / `Numeric(5,2)`| NOT NULL, `>= 0` | `0.00` | Points deducted due to verified lateness. | `0.00` |
| `bonus_points` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `>= 0` | `0.00` | Discretionary instructor bonus points. | `0.00` |
| `final_score` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `>= 0` | None | Final grade: `clamp(raw - penalty + bonus, 0, max)`. | `95.00` |
| `is_final` | `BOOLEAN` / `Boolean` | NOT NULL | `FALSE` | Whether grade is finalized and released. | `TRUE` |
| `grade_status` | `grade_status` / `Enum` | NOT NULL | `'provisional'`| Workflow status of grade. | `published` |
| `graded_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Evaluation completion timestamp. | `2026-10-17 14:00:00+00` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Record creation audit timestamp. | `2026-10-17 14:00:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last grade revision timestamp. | `2026-10-17 14:00:00+00` |

---

### 3.10. `grade_criterion_score`
Granular rubric itemization for transparent evaluations.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `score_id` | `VARCHAR(128)` / `String(128)`| PK, NOT NULL | None | Format: `GCS-<grade-id>-NN`. | `GCS-GRD-SUB-...-01` |
| `grade_id` | `VARCHAR(112)` / `String(112)`| FK (`grade.grade_id`), NOT NULL | None | Parent grade record. Cascades on delete. | `GRD-SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `criterion_id` | `VARCHAR(96)` / `String(96)` | FK (`rubric_criterion.criterion_id`), NOT NULL | None | Rubric criterion being evaluated. | `CRT-RUB-ASN-2026-000001-01-01` |
| `score_awarded` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `>= 0` | None | Score awarded; cannot exceed `criterion.max_points`.| `24.00` |
| `evaluator_comment`| `TEXT` / `Text` | NULLABLE | None | Criterion-specific justification or feedback. | `Excellent modularization; minor naming issue.` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Evaluation timestamp. | `2026-10-17 13:55:00+00` |

*Table Constraint*: `CONSTRAINT uq_grade_criterion UNIQUE (grade_id, criterion_id)`

---

### 3.11. `feedback`
Qualitative feedback and mentoring commentary attached to a grade.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `feedback_id` | `VARCHAR(128)` / `String(128)`| PK, NOT NULL | None | Format: `FBK-<grade-id>-NN`. | `FBK-GRD-SUB-...-01` |
| `grade_id` | `VARCHAR(112)` / `String(112)`| FK (`grade.grade_id`), NOT NULL | None | Associated grade assessment. | `GRD-SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `submission_id` | `VARCHAR(96)` / `String(96)` | FK (`submission.submission_id`), NOT NULL | None | Target submission attempt. | `SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `author_id` | `VARCHAR(64)` / `String(64)` | NOT NULL | None | Staff member authoring commentary. | `USR-INST-0042` |
| `visibility` | `feedback_visibility` / `Enum`| NOT NULL | `'learner_visible'`| Controls whether notes are visible to student. | `learner_visible` |
| `general_comments`| `TEXT` / `Text` | NOT NULL | None | Comprehensive review summary. | `Strong submission demonstrating high mastery.` |
| `strengths` | `TEXT` / `Text` | NULLABLE | None | Highlighted positive techniques. | `Robust exception handling in streaming consumer.`|
| `areas_for_improvement`| `TEXT` / `Text` | NULLABLE | None | Actionable guidance for future deliverables. | `Add load testing under simulated network latency.`|
| `published_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Release timestamp. | `2026-10-17 14:05:00+00` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Feedback creation timestamp. | `2026-10-17 14:05:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Feedback edit timestamp. | `2026-10-17 14:05:00+00` |

---

### 3.12. `resubmission`
Tracks subsequent attempts superseding prior submission attempts.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `resubmission_id`| `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Deterministic identifier format: `RSB-YYYY-NNNNNN`.| `RSB-2026-000001` |
| `original_submission_id`| `VARCHAR(96)` / `String(96)`| FK (`submission.submission_id`), NOT NULL | None | Initial attempt (attempt 1). | `SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `new_submission_id` | `VARCHAR(96)` / `String(96)` | FK (`submission.submission_id`), NOT NULL, UNIQUE | None | Subsequent attempt (attempt 2+). | `SUB-ASN-2026-000001-LNR-2026-000001-02` |
| `reason` | `TEXT` / `Text` | NOT NULL | None | Learner's justification for resubmission. | `Addressed feedback regarding dead-letter queues.` |
| `change_summary` | `TEXT` / `Text` | NULLABLE | None | Summary of code / document diffs. | `Refactored consumer.py to include retry policies.`|
| `approved_by` | `VARCHAR(64)` / `String(64)` | NULLABLE | None | Staff member authorizing attempt if required. | `USR-INST-0042` |
| `status` | `resubmission_status` / `Enum`| NOT NULL | `'submitted'` | Status of resubmission lifecycle. | `submitted` |
| `requested_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | When resubmission was initiated. | `2026-10-17 16:30:00+00` |
| `reviewed_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NULLABLE | None | When staff reviewed the resubmission request. | `2026-10-17 17:00:00+00` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Record creation timestamp. | `2026-10-17 16:30:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last update timestamp. | `2026-10-17 17:00:00+00` |

---

### 3.13. `appeal`
Formal administrative challenge filed by a student contesting an evaluation.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `appeal_id` | `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Mandatory exact format: `APP-YYYY-NNNNNN`. | `APP-2026-000001` |
| `submission_id` | `VARCHAR(96)` / `String(96)` | FK (`submission.submission_id`), NOT NULL | None | Contested submission attempt. | `SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `grade_id` | `VARCHAR(112)` / `String(112)`| FK (`grade.grade_id`), NOT NULL | None | Contested grade record. | `GRD-SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `learner_id` | `VARCHAR(32)` / `String(32)` | FK (`learner.learner_id`), NOT NULL | None | Learner lodging the dispute. | `LNR-2026-000001` |
| `reviewed_by` | `VARCHAR(64)` / `String(64)` | NULLABLE | None | Academic arbiter or committee lead reviewing. | `USR-DEAN-0012` |
| `status` | `appeal_status` / `Enum` | NOT NULL | `'submitted'` | Stage in dispute resolution workflow. | `approved` |
| `reason_category`| `appeal_reason_category` / `Enum`| NOT NULL | None | Formal classification of appeal basis. | `calculation_error` |
| `learner_statement`| `TEXT` / `Text` | NOT NULL | None | Detailed argument submitted by student. | `The rubric criterion points total 95, not 85.` |
| `contested_criteria`| `JSONB` / `JSONB` | NULLABLE | None | Array of specific `criterion_id`s challenged. | `["CRT-RUB-ASN-2026-000001-01-03"]` |
| `original_grade` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NOT NULL, `>= 0` | None | Frozen snapshot of final score prior to appeal. | `85.00` |
| `requested_grade`| `NUMERIC(5, 2)` / `Numeric(5,2)` | NULLABLE, `>= 0` | None | Grade requested by student. | `95.00` |
| `final_grade` | `NUMERIC(5, 2)` / `Numeric(5,2)` | NULLABLE, `>= 0` | None | Adjudicated final score post-review. | `95.00` |
| `decision_notes` | `TEXT` / `Text` | NULLABLE | None | Official written decision and justification. | `Verified tally error in Criterion 3; score adjusted.`|
| `submitted_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Lodging timestamp. Must be within appeal window. | `2026-10-18 09:00:00+00` |
| `resolved_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NULLABLE | None | Resolution timestamp. | `2026-10-19 11:30:00+00` |
| `created_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Audit creation timestamp. | `2026-10-18 09:00:00+00` |
| `updated_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Last status update timestamp. | `2026-10-19 11:30:00+00` |

---

### 3.14. `submission_status_history`
Append-only temporal log of all lifecycle transitions for a submission.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `history_id` | `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Deterministic identifier format: `SSH-YYYY-NNNNNN`.| `SSH-2026-000001` |
| `submission_id` | `VARCHAR(96)` / `String(96)` | FK (`submission.submission_id`), NOT NULL | None | Submission being audited. Cascades on delete. | `SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `old_status` | `submission_status` / `Enum` | NULLABLE | None | Preceding lifecycle status (NULL for initial creation).| `submitted` |
| `new_status` | `submission_status` / `Enum` | NOT NULL | None | Subsequent lifecycle status. | `under_review` |
| `changed_by` | `VARCHAR(64)` / `String(64)` | NOT NULL | None | Actor initiating transition (`system`, user ID). | `USR-INST-0042` |
| `change_reason` | `TEXT` / `Text` | NULLABLE | None | Contextual reason for transition. | `Evaluator opened submission grading interface.` |
| `changed_at` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Immutable event timestamp in UTC. | `2026-10-16 10:15:00+00` |

---

### 3.15. `audit_log`
Global immutable security and operational audit ledger.

| Column Name | Data Type (PG / ORM) | Constraints | Default | Description & Business Rules | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `audit_id` | `VARCHAR(32)` / `String(32)` | PK, NOT NULL | None | Deterministic identifier format: `AUD-YYYY-NNNNNN`.| `AUD-2026-000001` |
| `entity_name` | `VARCHAR(64)` / `String(64)` | NOT NULL | None | Target database entity name (e.g., `grade`, `appeal`).| `grade` |
| `entity_id` | `VARCHAR(128)` / `String(128)`| NOT NULL | None | Primary key of target entity being modified. | `GRD-SUB-ASN-2026-000001-LNR-2026-000001-01` |
| `action` | `audit_action_type` / `Enum` | NOT NULL | None | Action performed. | `GRADE_OVERRIDE` |
| `actor_id` | `VARCHAR(64)` / `String(64)` | NOT NULL | None | User or automated service ID performing operation. | `USR-DEAN-0012` |
| `actor_role` | `VARCHAR(32)` / `String(32)` | NOT NULL | `'system'` | Role of actor at execution time. | `academic_committee` |
| `timestamp` | `TIMESTAMPTZ` / `DateTime(tz=True)` | NOT NULL | `CURRENT_TIMESTAMP` | Tamper-proof event timestamp in UTC. | `2026-10-19 11:30:00+00` |
| `old_values` | `JSONB` / `JSONB` | NULLABLE | None | JSON snapshot of entity state prior to mutation. | `{"final_score": 85.00, "grade_status": "published"}` |
| `new_values` | `JSONB` / `JSONB` | NULLABLE | None | JSON snapshot of entity state post mutation. | `{"final_score": 95.00, "grade_status": "revised"}` |
| `client_ip` | `VARCHAR(45)` / `String(45)` | NULLABLE | None | IPv4 or IPv6 client origin address. | `192.168.1.104` |
| `user_agent` | `TEXT` / `Text` | NULLABLE | None | Browser user-agent or API client identifier. | `Mozilla/5.0 (Windows NT 10.0; Win64; x64)...` |
