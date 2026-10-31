# EduFlow – Business Rules, Exception Governance & Synthetic Data Engineering

## 1. Core Domain Business Rules

The **EduFlow** platform enforces deterministic business rules across the academic lifecycle. These rules are guaranteed at the database constraint layer, verified within Pydantic domain models, and validated via Pandas assertions during ETL/batch processing.

---

### BR-01: Timezone-Aware Due Dates & Cutoff Normalization
1. **Universal UTC Storage**: All timestamps (`due_date`, `cutoff_date`, `submitted_at`, `graded_at`, `resolved_at`) MUST be persisted in PostgreSQL as `TIMESTAMPTZ` normalized to UTC.
2. **Contextual Localization**:
   - Course-level deadlines are configured with an associated IANA timezone (e.g., `America/New_York`, `Asia/Kolkata`).
   - If a course sets a deadline as `2026-10-15 23:59:59 America/New_York`, the API converts this into UTC (`2026-10-16 03:59:59+00` or `2026-10-16 04:59:59+00` depending on Daylight Saving Time) prior to persistence.
   - Learner interfaces display the deadline localized to the learner's personal timezone, alongside a countdown and explicit UTC reference.
3. **Hard Cutoff Constraint**:
   - Every assignment MUST have a `cutoff_date` satisfying:
     $$\text{cutoff\_date} \ge \text{due\_date}$$
   - Any submission attempt timestamped where:
     $$t_{\text{submission}} > \text{cutoff\_date}$$
     MUST be unconditionally rejected with HTTP 403 / `SubmissionCutoffExceededException`.

---

### BR-02: Late Submission Penalties & Grace Period Algorithm
1. **Grace Period Buffer**:
   - Assignments configure a `grace_period_minutes` (default: 15 minutes) to protect against client network latency and clock jitter.
   - If $t_{\text{submission}} \le \text{due\_date} + \Delta t_{\text{grace}}$, then:
     $$\text{is\_late} = \text{FALSE}, \quad \text{late\_penalty\_percentage} = 0.00$$
2. **Sliding Scale Penalty Calculation**:
   - If $t_{\text{submission}} > \text{due\_date} + \Delta t_{\text{grace}}$, then:
     $$\text{is\_late} = \text{TRUE}$$
     $$\Delta t_{\text{late}} = t_{\text{submission}} - \text{due\_date}$$
   - Lateness in fractional 24-hour days:
     $$\text{DaysLate} = \left\lceil \frac{\Delta t_{\text{late}} - \Delta t_{\text{grace}}}{86400 \text{ seconds}} \right\rceil$$
   - Penalty calculation capped by `max_late_days`:
     $$\text{CappedDays} = \min(\text{DaysLate}, \text{max\_late\_days})$$
     $$\text{late\_penalty\_percentage} = \min(\text{CappedDays} \times \text{late\_penalty\_per\_day}, 100.00)$$
3. **Frozen Submission Metadata**:
   - `is_late`, `late_duration_seconds`, and `late_penalty_percentage` are calculated once and immutably written into the `submission` record upon receipt. Graders CANNOT alter these system metrics manually.

---

### BR-03: Missing Artifact Detection & Pre-Flight Validation
1. **Artifact Requirement Matrix**:
   - An assignment defines an immutable array of required artifact types:
     $$\text{required\_artifact\_types} \subseteq \{\text{'code\_repository'}, \text{'report\_pdf'}, \text{'dataset\_csv'}, \text{'video\_presentation'}, \text{'supplementary\_zip'}\}$$
2. **Pre-Submission Verification Gate**:
   - Before a submission status can transition from `draft` to `submitted`, the system executes an automated artifact verification check:
     $$\forall \tau \in \text{required\_artifact\_types}, \quad \exists a \in \text{SubmissionArtifacts} \text{ such that } a.\text{artifact\_type} = \tau$$
   - In addition, every artifact must satisfy:
     $$a.\text{file\_size\_bytes} > 0 \quad \land \quad a.\text{checksum\_sha256} \ne \text{NULL} \quad \land \quad a.\text{is\_verified} = \text{TRUE}$$
3. **Missing Artifact Rejection**:
   - If any required artifact type is missing or corrupted, the submission attempt is blocked, returning HTTP 422 with a structured error listing missing types:
     `{"error": "MISSING_REQUIRED_ARTIFACTS", "missing": ["report_pdf"]}`.

---

### BR-04: Rubric Configuration & Mathematical Consistency
1. **Rubric-to-Assignment Point Parity**:
   - The sum of all criteria maximum points in a rubric MUST equal the assignment's maximum score:
     $$\sum_{i=1}^{k} \text{criterion}_i.\text{max\_points} = \text{rubric}.\text{total\_points} = \text{assignment}.\text{max\_score}$$
   - Any attempt to publish an assignment where this condition is false raises `RubricTotalPointsMismatchException`.
2. **Criteria Weight Normalization**:
   - Criteria weights $w_i > 0$ serve as multipliers if weighted scoring is enabled. For standard additive rubrics, $w_i = 1.00$.

---

### BR-05: Rubric-Based Grading & Final Score Calculation
1. **Itemized Evaluation**:
   - Every grade requires an itemized score for each active rubric criterion:
     $$0 \le \text{score\_awarded}_i \le \text{criterion}_i.\text{max\_points}$$
2. **Raw Score Aggregation**:
   $$\text{RawScore} = \sum_{i=1}^{k} \text{score\_awarded}_i$$
   $$\text{RawScore} \le \text{assignment}.\text{max\_score}$$
3. **Penalty Deduction & Clamping**:
   - Late penalty points are deducted from the raw score:
     $$\text{LatePenaltyPoints} = \text{RawScore} \times \left(\frac{\text{submission}.\text{late\_penalty\_percentage}}{100.00}\right)$$
   - Discretionary bonus points $B \ge 0$ may be added by authorized instructors.
   - Final score is bounded strictly within $[0, \text{max\_score}]$:
     $$\text{FinalScore} = \max\Big(0, \min\big(\text{RawScore} - \text{LatePenaltyPoints} + B, \; \text{assignment}.\text{max\_score}\big)\Big)$$
4. **Idempotence & Immutability**:
   - Re-running the grading formula with identical inputs produces the identical `final_score`.
   - The grade record is assigned the deterministic primary key `GRD-<submission-id>`.

---

### BR-06: Resubmission Governance & Attempt Policies
1. **Permissible Attempt Limits**:
   - The assignment attribute `max_resubmissions` governs how many subsequent attempts a learner may execute after attempt 1.
   - If `max_resubmissions = 1`, the maximum allowed `attempt_number` is 2.
2. **Cutoff Precedence**:
   - No resubmission can be created after the assignment's `cutoff_date`, even if the learner has unused resubmission attempts remaining.
3. **Historical Preservation**:
   - Attempt 1 remains completely immutable in `submission` with its associated artifacts, grades, and feedback.
   - The new attempt generates a new `submission` record with `attempt_number = 2`, linked to attempt 1 via the `resubmission` table (`RSB-YYYY-NNNNNN`).
4. **Scoring Policy**:
   - Default academic policy: **Latest Attempt Governs Final Course Standing** (with historical audit preserved for GPA recalculation or instructor review).

---

### BR-07: Academic Appeal Lifecycle & Atomic Adjustment
1. **Eligibility Window**:
   - An appeal can only be lodged against a grade whose `grade_status = 'published'`.
   - Lodging MUST occur within the active appeal window:
     $$t_{\text{appeal}} \le \text{grade}.\text{graded\_at} + \Delta t_{\text{appeal\_window}} \quad (\text{default: 7 calendar days})$$
2. **Single Active Appeal**:
   - A submission cannot have more than one non-terminal appeal (`status IN ('submitted', 'under_review')`).
3. **Adjudication Outcomes**:
   - **`rejected`**: Original grade is upheld; appeal notes recorded; status moves to `rejected`.
   - **`approved`**: Grade is adjusted. The update to `grade.final_score` and status transition `grade_status = 'revised'` MUST execute inside an atomic database transaction that generates an immutable `AuditLog` entry.

---

### BR-08: Universal Immutability & Audit Logging
1. **Prohibition of Silent Mutation**:
   - Neither application code nor database administrators may execute un-audited `UPDATE` or `DELETE` statements on `submission`, `grade`, or `appeal`.
2. **Audit Payload Requirements**:
   - Every modification to sensitive academic records must record:
     - `entity_name`, `entity_id`
     - `action` (`INSERT`, `UPDATE`, `GRADE_OVERRIDE`, `APPEAL_DECISION`)
     - `actor_id`, `actor_role`
     - `timestamp` (UTC)
     - Full JSON snapshot of `old_values` and `new_values`
     - Client network telemetry (`client_ip`, `user_agent`)

---

## 2. Exception Scenarios & Governance Protocols

The table below details validation rules, error codes, HTTP status mapping, and rollback handling for system exceptions—including all four mandatory architectural edge cases.

| Scenario ID | Exception Title | Trigger Condition | System Validation Check | Handling & Mitigation Protocol | Audit & State Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EX-01** | **Submission by Unenrolled Learner** | A user attempts to submit artifacts for an assignment without active course enrollment. | `SELECT 1 FROM enrollment WHERE learner_id = :lid AND course_id = :cid AND status = 'active'` returns zero rows. | Abort transaction immediately. Return HTTP 403 Forbidden with code `ERR_UNENROLLED_LEARNER`. No submission or artifact records created. | Security log written to `AuditLog` recording unauthorized submission attempt with actor IP. |
| **EX-02** | **Grade Exceeding Rubric Maximum** | Evaluator submits criteria scores summing to $> \text{assignment}.\text{max\_score}$ or criterion score $> \text{criterion}.\text{max\_points}$. | 1. `score_awarded > criterion.max_points`<br>2. `raw_score > rubric.total_points`<br>3. `final_score > assignment.max_score` | Pydantic validator intercepts and database `CHECK` constraint triggers. Abort transaction. Return HTTP 422 Unprocessable Entity with itemized breakdown of exceeding criteria. | Grade remains in previous state. Logged as validation failure. |
| **EX-03** | **Late Penalty Applied Twice** | Regrading or appeal processing reapplies late penalty to an already penalized score, compounding deductions. | Lateness penalty must be derived strictly as a function of the immutable `submission.late_penalty_percentage` and raw score: `penalty = raw_score * (pct / 100)`. | Evaluation service computes penalty idempotently. If `grade.late_penalty_applied` exists, verify it matches expected calculation rather than subtracting iteratively. Mutex / transaction lock on grade row prevents race condition. | Any recalculated grade logs single idempotent deduction in `AuditLog`. |
| **EX-04** | **Appeal Grade Modification Without Audit** | An API call or script attempts to update `grade.final_score` following an appeal without writing to `audit_log`. | Enforced via an **Atomic Transaction Manager** and a PostgreSQL trigger: an update to `grade` with `grade_status = 'revised'` MUST be accompanied by an `audit_log` insert with matching `entity_id` within the same transaction. | If audit logging fails or is omitted, transaction encounters `AuditLogMissingException` and issues an unconditional `ROLLBACK`. Return HTTP 500 Internal Server Error. | Zero change committed. System raises high-severity security alert. |
| **EX-05** | **Missing Mandatory Artifacts** | Learner attempts to finalize submission without required file types (e.g., missing `report_pdf`). | Set comparison: `required_artifact_types \subseteq uploaded_artifact_types`. | Reject status transition `draft -> submitted`. Return HTTP 422 with list of missing artifacts. | Status remains `draft`. Event logged in `SubmissionStatusHistory`. |
| **EX-06** | **Submission Past Cutoff Date** | Learner submits after `assignment.cutoff_date`. | $t_{\text{submission}} > \text{cutoff\_date}$. | Unconditional submission lockout. Return HTTP 403 Forbidden with code `ERR_DEADLINE_EXCEEDED`. | Rejection recorded with timestamp and learner ID. |
| **EX-07** | **Exceeded Resubmission Limit** | Learner attempts attempt $N+1$ where $N \ge \text{max\_resubmissions} + 1$. | `SELECT COUNT(*) FROM submission WHERE assignment_id = :aid AND learner_id = :lid` exceeds allowable attempts. | Block creation of new attempt. Return HTTP 400 Bad Request with code `ERR_RESUBMISSION_LIMIT_REACHED`. | Action denied. |
| **EX-08** | **Appeal Filed Outside Window** | Learner files appeal 14 days after grade publication (window is 7 days). | $t_{\text{appeal}} > \text{graded\_at} + 7 \text{ days}$. | Reject appeal submission. Return HTTP 400 Bad Request with code `ERR_APPEAL_WINDOW_EXPIRED`. | Rejected attempt recorded in `AuditLog`. |

---

## 3. Deterministic Synthetic Data Generator Plan

To rigorously benchmark system performance, test analytics queries, and validate the UI under realistic load, a synthetic data generator will produce enterprise-scale datasets.

### 3.1. Target Volume & Generation Constraints
- **Assignments**: $1,000$
- **Learners**: $10,000$
- **Submissions**: $30,000$
- **Courses**: $50$ (averaging 20 assignments each)
- **Deterministic Master Random Seed**: `20261022`
- **Tooling**: Python 3.11+, NumPy (vectorized distribution sampling), Faker (realistic student profiles), Pandas (validation & export).

---

### 3.2. Statistical & Behavioral Distribution Models

#### 1. Learner Competency ($\theta$)
Each learner $i$ is assigned a latent competency parameter sampled from a Beta distribution reflecting typical academic mastery:
$$\theta_i \sim \text{Beta}(\alpha=4.5, \beta=2.0) \implies \mathbb{E}[\theta] \approx 0.692$$
Scaled to a $[0, 100]$ score baseline:
$$\text{BaseCompetency}_i = 50 + 50 \times \theta_i \quad (\text{Mean} \approx 84.6, \text{StdDev} \approx 8.2)$$

#### 2. Submission Timing Distribution
Submission time relative to assignment deadline $D$ follows a composite distribution:
- **80% On-Time Submissions**:
  $$t_{\text{submission}} = D - |X|, \quad X \sim \text{Normal}(\mu = 14\text{ hours}, \sigma = 8\text{ hours})$$
  Bounded such that $t_{\text{submission}} \le D$.
- **15% Late Submissions (Within Cutoff)**:
  $$t_{\text{submission}} = D + Y, \quad Y \sim \text{Exponential}(\lambda = 1.2\text{ days})$$
  Capped at $D + \text{max\_late\_days}$.
- **5% Edge Cases**:
  - Exactly within the 15-minute grace period ($D < t \le D + 15\text{m}$).
  - Incomplete draft submissions with missing artifacts.

#### 3. Scoring & Evaluation Model
Given assignment max score $M = 100$, student competency $\theta_i$, and assignment difficulty factor $\delta_j \sim \text{Uniform}(0.9, 1.1)$:
$$\text{RawScore}_{i,j} = \min\Big(M, \max\big(0, \text{Normal}(\mu = \text{BaseCompetency}_i \times \delta_j, \sigma = 6.0)\big)\Big)$$
Criteria breakdown decomposes $\text{RawScore}_{i,j}$ proportionally across the rubric's criteria weights.

#### 4. Resubmissions & Appeals Volume
- **Resubmissions**: Approximately $10\%$ of initial submissions ($3,000$ records) trigger a second attempt (`attempt_number = 2`), primarily driven by lower initial scores ($< 70$).
- **Appeals**: Approximately $5\%$ of graded submissions ($1,500$ records) lodge formal appeals:
  - $60\%$ rejected (original grade upheld).
  - $30\%$ approved with minor adjustment ($+3$ to $+8$ points).
  - $10\%$ approved with significant adjustment due to rubric calculation error.

---

### 3.3. Ground Truth vs. Application Input Separation

To enable rigorous data quality testing and grading algorithm validation, generated data is partitioned into two isolated outputs:

```
data/
├── ground_truth/                  <-- Clean, canonical reference data
│   ├── ground_truth_learners.parquet
│   ├── ground_truth_assignments.parquet
│   ├── ground_truth_expected_scores.parquet
│   ├── ground_truth_submission_timing.parquet
│   └── ground_truth_appeal_benchmarks.parquet
│
└── application_input/             <-- Operational database import files (with real-world noise)
    ├── courses.csv
    ├── learners.csv
    ├── enrollments.csv
    ├── assignments.csv
    ├── rubrics.csv
    ├── rubric_criteria.csv
    ├── submissions.csv
    ├── submission_artifacts.csv
    ├── grades.csv
    ├── grade_criterion_scores.csv
    ├── feedback.csv
    ├── resubmissions.csv
    ├── appeals.csv
    ├── submission_status_history.csv
    └── audit_logs.csv
```

#### Ground Truth Artifacts Purpose:
1. **Benchmark Validation**: `ground_truth_expected_scores.parquet` holds the theoretical unpenalized scores and pure lateness durations before system noise.
2. **Quality Assertions**: Enables running automated Pandas ETL tests to verify that the application layer calculated penalties with $100\%$ mathematical fidelity to the business rules.
3. **Model Evaluation**: Provides clean labeling for potential ML-assisted grading or anomaly detection services.
