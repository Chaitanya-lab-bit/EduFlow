# Phase 3 – Synthetic Data Generation

## Overview

The synthetic data generation engine (`data_generation/`) produces fully deterministic, statistically realistic datasets for the EduFlow / YottaFlex 72-hour challenge. Every run with the same `--seed` produces **byte-identical** CSV, JSON, and SQL exports.

---

## Quick Start

```bash
# Activate the backend virtual environment
cd backend && .\\venv\\Scripts\\activate && cd ..

# Generate starter dataset (5 courses, 100 learners, 20 assignments, 200 submissions)
python data_generation/main.py --profile starter

# Generate full dataset (100 courses, 10,000 learners, 1,000 assignments, 30,000 submissions)
python data_generation/main.py --profile full

# Custom seed (default: 20261022)
python data_generation/main.py --profile full --seed 42
```

---

## Architecture

```
data_generation/
├── config.py                        # DatasetConfig profiles (STARTER / FULL)
├── main.py                          # Orchestrator & CLI entry-point
├── generators/
│   ├── master_data_generator.py     # Courses, Learners (β-distributed competency)
│   ├── enrollment_generator.py      # Course–Learner associations
│   ├── assignment_generator.py      # Assignments, Rubrics, Criteria (exact point sums)
│   ├── submission_generator.py      # Submissions + Status Histories
│   ├── artifact_generator.py        # Submission Artifacts (SHA-256 checksums)
│   ├── grade_generator.py           # Grades, Criterion Scores, Feedback
│   ├── feedback_generator.py        # Qualitative mentor comments
│   ├── resubmission_generator.py    # Attempt-2 resubmission workflows
│   ├── appeal_generator.py          # Appeals + Atomic Audit Logs
│   └── anomaly_generator.py         # 4 mandatory ground-truth anomalies (EX-01 → EX-04)
├── validators/
│   └── data_validator.py            # 8-category validation framework
└── exports/
    └── exporter.py                  # CSV, JSON, PostgreSQL SQL seed writer
```

### Generation Topology (Parent → Child)

```
Courses ──► Learners ──► Enrollments
                               │
              Assignments ◄────┘
                    │
                 Rubrics ──► Criteria
                    │
               Submissions ──► Artifacts, StatusHistories
                    │
                 Grades ──► CriterionScores ──► Feedback
                    │
              Resubmissions ──► Grades (attempt 2)
                    │
                Appeals ──► AuditLogs (approved only)
                    │
             Anomalies (ground_truth, isolated)
```

---

## Statistical Distributions

| Entity | Distribution | Parameters |
|---|---|---|
| Learner competency (θ) | Beta(α=5, β=2) rescaled | → [50, 100] |
| Submission timing | Mixture (3 components) | 80% on-time, 5% grace, 15% late |
| On-time hours early | Normal(μ=14h, σ=8h), bounded | [0.1h, 168h] |
| Late duration | Exponential(λ=1/1.2 days) | clipped to cutoff |
| Grade score | Derived from θ + rubric noise | N(θ, 5²) per criterion |
| Resubmission rate | 10% of graded submissions | deterministic |
| Appeal rate | 5% of graded submissions | deterministic |
| Appeal approval | 40% of filed appeals | deterministic |

---

## Fixed Random Seed

All generators accept an integer `seed` (default **`20261022`**). The NumPy `default_rng` is seeded once per generator invocation and all draws are made in topological order, guaranteeing reproducibility across runs and Python versions (NumPy ≥ 1.17 PCG64 bit-generator).

---

## Dataset Profiles

| Profile | Courses | Learners | Assignments | Submissions |
|---|---|---|---|---|
| `starter` | 5 | 100 | 20 | 200 |
| `full` | 100 | 10,000 | 1,000 | 30,000 |

The starter profile is used for automated testing and takes < 1 second.  
The full profile meets the YottaFlex challenge targets and takes ~10 seconds.

---

## ID Conventions

All IDs follow zero-padded formats per the challenge specification:

| Entity | Format | Example |
|---|---|---|
| Course | `CRS-2026-NNNNNN` | `CRS-2026-000001` |
| Learner | `LNR-2026-NNNNNN` | `LNR-2026-000042` |
| Enrollment | `ENR-2026-NNNNNN` | `ENR-2026-003210` |
| Assignment | `ASN-2026-NNNNNN` | `ASN-2026-000007` |
| Rubric | `RUB-{assignment_id}-VNN` | `RUB-ASN-2026-000007-V01` |
| Criterion | `CRT-{rubric_id}-NN` | `CRT-RUB-...-V01-01` |
| Submission | `SUB-{assignment_id}-{learner_id}-NN` | `SUB-ASN-...-LNR-...-01` |
| Grade | `GRD-{submission_id}` | `GRD-SUB-ASN-...` |
| Resubmission | `{submission_id}-R` | `SUB-...-01-R` |
| Appeal | `APL-{grade_id}-NN` | `APL-GRD-...-01` |
| Audit Log | `AUD-2026-NNNNNN` | `AUD-2026-000001` |

---

## Business Rule Enforcement

The generator faithfully implements all domain business rules from `docs/business_rules.md`:

| Rule | Implementation |
|---|---|
| BR-01: One active rubric per assignment | `is_active=True` flag; v2 rubric marked `is_active=False` |
| BR-02: Grace period waiver | `is_late` rechecked after drawing late timing; corrected to `False` if ≤ grace window |
| BR-03: Late penalty formula | `penalty = raw_score × (late_pct / 100)`, applied once |
| BR-04: Final score clamped | `final_score = clamp(raw - penalty + bonus, 0, max_score)` |
| BR-05: Appeal audit atomicity | Each approved appeal writes exactly 1 `APPEAL_DECISION` audit log entry |
| BR-06: Grade status lifecycle | `pending → graded → published`; appeal-approved → `revised` |
| BR-07: Resubmission limit | Max 1 resubmission per submission (attempt_number ≤ 2) |

---

## Ground-Truth Anomaly Scenarios

Four mandatory anomaly records are generated in an **isolated** ground-truth dataset and never inserted into the operational tables:

| ID | Scenario | Trigger |
|---|---|---|
| EX-01 | Unenrolled learner submission | Learner submits for an assignment in a course they never enrolled in |
| EX-02 | Grade exceeding rubric maximum | `final_score > 100.0` (max_score) for a standard assignment |
| EX-03 | Duplicate late penalty deduction | `late_penalty_applied = 2 × correct_value`, `final_score` computed on doubled penalty |
| EX-04 | Appeal without audit log | Approved appeal that has no corresponding `APPEAL_DECISION` audit log entry |

Ground-truth records are exported separately to:
```
exports/{profile}/ground_truth/anomalies.csv
exports/{profile}/ground_truth/anomalies.json
```

---

## Exports

After generation, outputs are written to `data_generation/exports/{profile}/`:

```
exports/starter/
├── seed.sql                # PostgreSQL INSERT statements (batched 500 rows)
├── courses.csv / .json
├── learners.csv / .json
├── enrollments.csv / .json
├── assignments.csv / .json
├── rubrics.csv / .json
├── rubric_criteria.csv / .json
├── submissions.csv / .json
├── submission_artifacts.csv / .json
├── submission_status_histories.csv / .json
├── grades.csv / .json
├── grade_criterion_scores.csv / .json
├── feedbacks.csv / .json
├── resubmissions.csv / .json
├── appeals.csv / .json
├── audit_logs.csv / .json
└── ground_truth/
    ├── anomalies.csv
    └── anomalies.json
```

---

## Validation Framework

The `DataValidator` runs 94 automated checks across 8 categories:

| # | Category | Checks |
|---|---|---|
| 1 | Primary Key Uniqueness | Duplicate IDs, duplicate (course, learner) enrollment pairs, duplicate submission_id in grades |
| 2 | Foreign Key Integrity | Orphaned submissions, criterion scores, feedback, resubmissions, appeals |
| 3 | Enum Values | Submission status, grade status, enrollment status, artifact type, appeal status |
| 4 | Date Ordering | submission ≤ cutoff, grade ≥ submission, rubric dates within course window |
| 5 | Grade Reconciliation | Criteria sum = raw_score; final_score formula for non-revised grades |
| 6 | Duplicate Penalty Detection | `late_penalty_applied ≠ raw_score × (pct/100)` (catches doubled deductions) |
| 7 | Lifecycle Transitions | Status history sequence: submitted → graded → published |
| 8 | Anomaly Labels | All 4 required EX- scenarios present in ground_truth |

---

## Test Suite

Three pytest modules are provided in `tests/`:

| File | Tests | Scope |
|---|---|---|
| `test_data_generation.py` | Generator unit tests per entity | Starter profile |
| `test_data_validation.py` | Validator correctness — clean + corrupt injection | Starter profile |
| `test_reproducibility.py` | SHA-256 checksum equality across 2 runs | Starter profile |

Run all tests:
```bash
pytest tests/test_data_generation.py tests/test_data_validation.py tests/test_reproducibility.py -v
```

**Expected result: 98 passed, 0 failed.**

---

## Dependencies

Added to `backend/requirements.txt`:

```
faker>=30.0.0
numpy>=1.26.0
pandas>=2.2.0
```

Install:
```bash
pip install -r backend/requirements.txt
```
