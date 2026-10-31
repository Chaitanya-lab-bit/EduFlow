"""
tests/test_data_generation.py

Tests that each generator module produces the expected number and structure of
records for both the starter and full dataset profiles.
"""
import sys
from pathlib import Path
import pytest
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_generation.config import STARTER_CONFIG, FULL_CONFIG
from data_generation.generators.master_data_generator import generate_courses, generate_learners
from data_generation.generators.enrollment_generator import generate_enrollments
from data_generation.generators.assignment_generator import generate_assignments_and_rubrics
from data_generation.generators.submission_generator import generate_submissions
from data_generation.generators.artifact_generator import generate_artifacts
from data_generation.generators.grade_generator import generate_grades
from data_generation.generators.feedback_generator import generate_feedback
from data_generation.generators.resubmission_generator import generate_resubmissions
from data_generation.generators.appeal_generator import generate_appeals
from data_generation.generators.anomaly_generator import generate_anomalies
from data_generation.main import generate_dataset

SEED = 20261022
CFG = STARTER_CONFIG


@pytest.fixture(scope="module")
def starter_data():
    """Full starter dataset — generated once, reused across all tests in module."""
    data, anomalies, report = generate_dataset(CFG)
    return data, anomalies, report


# ──────────────────────────────────────────────────────────────────────────────
# 1. Master data generators
# ──────────────────────────────────────────────────────────────────────────────

class TestCourseGenerator:
    def test_correct_count(self):
        courses = generate_courses(CFG.num_courses, SEED)
        assert len(courses) == CFG.num_courses

    def test_unique_ids(self):
        courses = generate_courses(CFG.num_courses, SEED)
        ids = [c["course_id"] for c in courses]
        assert len(ids) == len(set(ids)), "Duplicate course IDs"

    def test_id_format(self):
        courses = generate_courses(CFG.num_courses, SEED)
        for c in courses:
            assert c["course_id"].startswith("CRS-2026-"), f"Bad ID format: {c['course_id']}"

    def test_date_ordering(self):
        from datetime import datetime
        courses = generate_courses(CFG.num_courses, SEED)
        for c in courses:
            start = datetime.fromisoformat(c["start_date"])
            end = datetime.fromisoformat(c["end_date"])
            assert end > start, f"Course {c['course_id']}: end_date not after start_date"

    def test_valid_status(self):
        from backend.models.enums import CourseStatus
        courses = generate_courses(CFG.num_courses, SEED)
        valid = {e.value for e in CourseStatus}
        for c in courses:
            assert c["status"] in valid


class TestLearnerGenerator:
    def test_correct_count(self):
        learners, comp_map = generate_learners(CFG.num_learners, SEED)
        assert len(learners) == CFG.num_learners

    def test_competency_map_size(self):
        learners, comp_map = generate_learners(CFG.num_learners, SEED)
        assert len(comp_map) == CFG.num_learners

    def test_competency_range(self):
        learners, comp_map = generate_learners(CFG.num_learners, SEED)
        for lid, comp in comp_map.items():
            assert 50.0 <= comp <= 100.0, f"Competency out of range for {lid}: {comp}"

    def test_unique_emails(self):
        learners, _ = generate_learners(CFG.num_learners, SEED)
        emails = [l["email"] for l in learners]
        assert len(emails) == len(set(emails)), "Duplicate learner emails"

    def test_unique_student_numbers(self):
        learners, _ = generate_learners(CFG.num_learners, SEED)
        snums = [l["student_number"] for l in learners]
        assert len(snums) == len(set(snums)), "Duplicate student numbers"

    def test_id_format(self):
        learners, _ = generate_learners(CFG.num_learners, SEED)
        for l in learners:
            assert l["learner_id"].startswith("LNR-2026-"), f"Bad ID: {l['learner_id']}"


class TestEnrollmentGenerator:
    def setup_method(self):
        self.courses = generate_courses(CFG.num_courses, SEED)
        self.learners, _ = generate_learners(CFG.num_learners, SEED)

    def test_minimum_enrollment_count(self):
        enrs, _ = generate_enrollments(
            self.courses, self.learners,
            CFG.min_enrollments_per_learner, CFG.max_enrollments_per_learner, SEED
        )
        assert len(enrs) >= CFG.num_learners * CFG.min_enrollments_per_learner

    def test_no_duplicate_pairs(self):
        enrs, _ = generate_enrollments(
            self.courses, self.learners,
            CFG.min_enrollments_per_learner, CFG.max_enrollments_per_learner, SEED
        )
        pairs = [(e["course_id"], e["learner_id"]) for e in enrs]
        assert len(pairs) == len(set(pairs)), "Duplicate (course_id, learner_id) pairs"

    def test_fk_integrity(self):
        enrs, _ = generate_enrollments(
            self.courses, self.learners,
            CFG.min_enrollments_per_learner, CFG.max_enrollments_per_learner, SEED
        )
        course_ids = {c["course_id"] for c in self.courses}
        learner_ids = {l["learner_id"] for l in self.learners}
        for e in enrs:
            assert e["course_id"] in course_ids
            assert e["learner_id"] in learner_ids

    def test_enrollment_map_matches_records(self):
        enrs, enr_map = generate_enrollments(
            self.courses, self.learners,
            CFG.min_enrollments_per_learner, CFG.max_enrollments_per_learner, SEED
        )
        assert len(enr_map) == len(enrs)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Assignment & Rubric generators
# ──────────────────────────────────────────────────────────────────────────────

class TestAssignmentRubricGenerator:
    def setup_method(self):
        self.courses = generate_courses(CFG.num_courses, SEED)

    def test_assignment_count(self):
        asns, _, _ = generate_assignments_and_rubrics(
            self.courses, CFG.num_assignments, CFG.criteria_per_rubric,
            CFG.additional_rubric_versions, SEED
        )
        assert len(asns) == CFG.num_assignments

    def test_rubric_count_at_least_one_per_assignment(self):
        asns, rubrics, _ = generate_assignments_and_rubrics(
            self.courses, CFG.num_assignments, CFG.criteria_per_rubric,
            CFG.additional_rubric_versions, SEED
        )
        rubric_aids = {r["assignment_id"] for r in rubrics}
        asn_ids = {a["assignment_id"] for a in asns}
        assert asn_ids == rubric_aids, "Some assignments missing a rubric"

    def test_criteria_count_per_rubric(self):
        asns, rubrics, criteria = generate_assignments_and_rubrics(
            self.courses, CFG.num_assignments, CFG.criteria_per_rubric,
            CFG.additional_rubric_versions, SEED
        )
        from collections import Counter
        counts = Counter(c["rubric_id"] for c in criteria)
        for rid, count in counts.items():
            assert count == CFG.criteria_per_rubric, f"Rubric {rid} has {count} criteria (expected {CFG.criteria_per_rubric})"

    def test_rubric_total_points_sum(self):
        asns, rubrics, criteria = generate_assignments_and_rubrics(
            self.courses, CFG.num_assignments, CFG.criteria_per_rubric,
            CFG.additional_rubric_versions, SEED
        )
        crit_by_rubric = {}
        for c in criteria:
            crit_by_rubric.setdefault(c["rubric_id"], []).append(c["max_points"])
        for r in rubrics:
            pts_sum = round(sum(crit_by_rubric.get(r["rubric_id"], [])), 2)
            assert abs(pts_sum - r["total_points"]) <= 0.02, \
                f"Rubric {r['rubric_id']} sum {pts_sum} != {r['total_points']}"

    def test_cutoff_after_due_date(self):
        from datetime import datetime
        asns, _, _ = generate_assignments_and_rubrics(
            self.courses, CFG.num_assignments, CFG.criteria_per_rubric,
            CFG.additional_rubric_versions, SEED
        )
        for a in asns:
            due = datetime.fromisoformat(a["due_date"])
            cutoff = datetime.fromisoformat(a["cutoff_date"])
            assert cutoff >= due, f"Assignment {a['assignment_id']}: cutoff < due_date"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Submission generators
# ──────────────────────────────────────────────────────────────────────────────

class TestSubmissionGenerator:
    def setup_method(self):
        self.courses = generate_courses(CFG.num_courses, SEED)
        learners, self.comp_map = generate_learners(CFG.num_learners, SEED)
        self.learners = learners
        self.enrollments, _ = generate_enrollments(
            self.courses, learners,
            CFG.min_enrollments_per_learner, CFG.max_enrollments_per_learner, SEED
        )
        self.assignments, self.rubrics, self.criteria = generate_assignments_and_rubrics(
            self.courses, CFG.num_assignments, CFG.criteria_per_rubric,
            CFG.additional_rubric_versions, SEED
        )
        self.submissions, self.status_histories = generate_submissions(
            self.assignments, self.enrollments, CFG.num_submissions, SEED
        )

    def test_target_submission_count(self):
        assert len(self.submissions) == CFG.num_submissions

    def test_no_duplicate_attempt1_pairs(self):
        pairs = [(s["assignment_id"], s["learner_id"]) for s in self.submissions if s["attempt_number"] == 1]
        assert len(pairs) == len(set(pairs)), "Duplicate (assignment_id, learner_id) attempt 1 pairs"

    def test_all_attempt1(self):
        for s in self.submissions:
            assert s["attempt_number"] == 1, f"Submission {s['submission_id']} not attempt 1"

    def test_late_penalty_logical(self):
        from datetime import datetime
        asn_map = {a["assignment_id"]: a for a in self.assignments}
        for s in self.submissions:
            asn = asn_map[s["assignment_id"]]
            sub_time = datetime.fromisoformat(s["submitted_at"])
            due_time = datetime.fromisoformat(asn["due_date"])
            grace_secs = asn["grace_period_minutes"] * 60
            from datetime import timedelta
            grace_deadline = due_time + timedelta(seconds=grace_secs)
            if sub_time <= grace_deadline:
                assert not s["is_late"], f"Sub {s['submission_id']}: before grace deadline but marked late"
                assert s["late_penalty_percentage"] == 0.0

    def test_no_submission_past_cutoff(self):
        from datetime import datetime
        asn_map = {a["assignment_id"]: a for a in self.assignments}
        for s in self.submissions:
            asn = asn_map[s["assignment_id"]]
            sub_time = datetime.fromisoformat(s["submitted_at"])
            cutoff_time = datetime.fromisoformat(asn["cutoff_date"])
            assert sub_time <= cutoff_time, f"Sub {s['submission_id']} past cutoff"

    def test_status_history_count(self):
        assert len(self.status_histories) == CFG.num_submissions


# ──────────────────────────────────────────────────────────────────────────────
# 4. Grade generator
# ──────────────────────────────────────────────────────────────────────────────

class TestGradeGenerator:
    def setup_method(self):
        self.courses = generate_courses(CFG.num_courses, SEED)
        learners, self.comp_map = generate_learners(CFG.num_learners, SEED)
        self.learners = learners
        self.enrollments, _ = generate_enrollments(
            self.courses, learners,
            CFG.min_enrollments_per_learner, CFG.max_enrollments_per_learner, SEED
        )
        self.assignments, self.rubrics, self.criteria = generate_assignments_and_rubrics(
            self.courses, CFG.num_assignments, CFG.criteria_per_rubric,
            CFG.additional_rubric_versions, SEED
        )
        self.submissions, _ = generate_submissions(
            self.assignments, self.enrollments, CFG.num_submissions, SEED
        )
        self.grades, self.crit_scores, _, _ = generate_grades(
            self.submissions, self.assignments, self.rubrics, self.criteria,
            self.comp_map, CFG.grade_rate, SEED
        )

    def test_grade_rate_approximately_correct(self):
        expected = int(CFG.num_submissions * CFG.grade_rate)
        actual = len(self.grades)
        assert abs(actual - expected) <= max(5, expected * 0.05), \
            f"Grade count {actual} far from expected {expected}"

    def test_unique_grade_ids(self):
        ids = [g["grade_id"] for g in self.grades]
        assert len(ids) == len(set(ids)), "Duplicate grade IDs"

    def test_unique_submission_per_grade(self):
        sub_ids = [g["submission_id"] for g in self.grades]
        assert len(sub_ids) == len(set(sub_ids)), "Duplicate submission_id in grades (1:1 violation)"

    def test_grade_id_format(self):
        for g in self.grades:
            assert g["grade_id"].startswith("GRD-"), f"Bad grade ID format: {g['grade_id']}"
            assert g["grade_id"] == f"GRD-{g['submission_id']}", "grade_id must be GRD-<submission_id>"

    def test_raw_score_bounds(self):
        for g in self.grades:
            assert 0 <= g["raw_score"] <= 100.0, f"raw_score {g['raw_score']} out of [0,100]"

    def test_criteria_sum_matches_raw_score(self):
        grade_crits = {}
        for cs in self.crit_scores:
            grade_crits.setdefault(cs["grade_id"], []).append(cs["score_awarded"])
        for g in self.grades:
            gid = g["grade_id"]
            if gid in grade_crits:
                total = round(sum(grade_crits[gid]), 2)
                assert abs(total - g["raw_score"]) <= 0.02, \
                    f"Grade {gid}: criteria sum {total} != raw_score {g['raw_score']}"

    def test_final_score_formula_for_baseline_grades(self):
        grade_sub_map = {g["submission_id"]: g for g in self.grades}
        asn_map = {a["assignment_id"]: a for a in self.assignments}
        for s in self.submissions:
            grd = grade_sub_map.get(s["submission_id"])
            if not grd or grd["grade_status"] == "revised":
                continue
            asn = asn_map[s["assignment_id"]]
            expected = round(
                max(0.0, min(grd["raw_score"] - grd["late_penalty_applied"] + grd["bonus_points"],
                             float(asn["max_score"]))),
                2
            )
            assert abs(grd["final_score"] - expected) <= 0.02, \
                f"Grade {grd['grade_id']}: final_score {grd['final_score']} != expected {expected}"


# ──────────────────────────────────────────────────────────────────────────────
# 5. Anomaly generator — correctness + isolation
# ──────────────────────────────────────────────────────────────────────────────

class TestAnomalyGenerator:
    def test_four_required_scenarios_present(self, starter_data):
        data, anomalies, report = starter_data
        scenario_ids = {a["scenario_id"] for a in anomalies}
        required = {"EX-01", "EX-02", "EX-03", "EX-04"}
        assert required == scenario_ids, f"Missing required scenarios: {required - scenario_ids}"

    def test_anomalies_not_in_main_dataset(self, starter_data):
        data, anomalies, report = starter_data
        main_sub_ids = {s["submission_id"] for s in data["submissions"]}

        # Only EX-01 must use a truly synthetic (non-existent) submission ID.
        # EX-02 and EX-03 deliberately reference real submissions to simulate
        # corrupted grade/penalty records on them.
        ex01 = next(a for a in anomalies if a["scenario_id"] == "EX-01")
        ex01_payload = ex01.get("record_payload", {})
        ex01_sid = ex01_payload.get("submission_id")
        if ex01_sid:
            assert ex01_sid not in main_sub_ids, (
                f"EX-01 anomaly submission {ex01_sid} leaked into main dataset — "
                "it must reference a learner with no real enrollment for that assignment"
            )

    def test_unenrolled_submission_references_nonexistent_enrollment(self, starter_data):
        data, anomalies, _ = starter_data
        enr_ids = {e["enrollment_id"] for e in data["enrollments"]}
        ex01 = next(a for a in anomalies if a["scenario_id"] == "EX-01")
        payload = ex01["record_payload"]
        assert payload["enrollment_id"] not in enr_ids, \
            "EX-01 anomaly uses a valid enrollment (should use an invalid one)"

    def test_grade_exceeding_rubric_maximum_exceeds_100(self, starter_data):
        _, anomalies, _ = starter_data
        ex02 = next(a for a in anomalies if a["scenario_id"] == "EX-02")
        payload = ex02["record_payload"]
        assert payload["final_score"] > 100.0, \
            f"EX-02 anomaly final_score {payload['final_score']} does not exceed max 100"

    def test_duplicate_penalty_compounds_deduction(self, starter_data):
        _, anomalies, _ = starter_data
        ex03 = next(a for a in anomalies if a["scenario_id"] == "EX-03")
        payload = ex03["record_payload"]
        raw = payload["raw_score"]
        penalty = payload["late_penalty_applied"]
        final = payload["final_score"]
        # The penalty should have been applied twice (corrupted formula)
        single_final = round(max(0.0, raw - (penalty / 2)), 2)
        assert abs(final - (raw - penalty)) <= 0.02, \
            f"EX-03 anomaly does not exhibit doubled penalty: raw={raw} penalty={penalty} final={final}"

    def test_ex04_appeal_has_no_matching_audit_log(self, starter_data):
        data, anomalies, _ = starter_data
        ex04 = next(a for a in anomalies if a["scenario_id"] == "EX-04")
        appeal_id = ex04["entity_id"]
        audit_entity_ids = {a["entity_id"] for a in data["audit_logs"]}
        # The anomalous appeal's grade_id should not appear in the normal audit_logs
        payload = ex04["record_payload"]
        grade_id = payload["grade_id"]
        # Verify the appeal_id itself is not in the normal dataset
        main_appeal_ids = {a["appeal_id"] for a in data["appeals"]}
        assert appeal_id not in main_appeal_ids, \
            f"EX-04 anomaly appeal {appeal_id} was inserted into main dataset"


# ──────────────────────────────────────────────────────────────────────────────
# 6. Volume & completeness checks
# ──────────────────────────────────────────────────────────────────────────────

class TestVolumeRequirements:
    def test_minimum_enrollments(self, starter_data):
        data, _, _ = starter_data
        count = len(data["enrollments"])
        expected_min = CFG.num_learners * CFG.min_enrollments_per_learner
        assert count >= expected_min, f"Enrollment count {count} < minimum {expected_min}"

    def test_rubric_count_meets_or_exceeds_assignments(self, starter_data):
        data, _, _ = starter_data
        # At minimum 1 rubric per assignment (active version)
        assert len(data["rubrics"]) >= CFG.num_assignments

    def test_criteria_count(self, starter_data):
        data, _, _ = starter_data
        # At minimum 1 rubric * 5 criteria per assignment
        min_criteria = CFG.num_assignments * CFG.criteria_per_rubric
        assert len(data["rubric_criteria"]) >= min_criteria

    def test_resubmissions_generated(self, starter_data):
        data, _, _ = starter_data
        assert len(data["resubmissions"]) > 0, "No resubmissions generated"

    def test_appeals_generated(self, starter_data):
        data, _, _ = starter_data
        assert len(data["appeals"]) > 0, "No appeals generated"

    def test_audit_logs_for_approved_appeals_only(self, starter_data):
        data, _, _ = starter_data
        approved_appeals = [a for a in data["appeals"] if a["status"] == "approved"]
        # Each approved appeal must have exactly 1 audit log entry with APPEAL_DECISION action
        audit_actions = [al for al in data["audit_logs"] if al["action"] == "APPEAL_DECISION"]
        assert len(audit_actions) == len(approved_appeals), \
            f"Audit log count {len(audit_actions)} != approved appeal count {len(approved_appeals)}"

    def test_all_graded_submissions_have_feedback(self, starter_data):
        data, _, _ = starter_data
        grade_ids = {g["grade_id"] for g in data["grades"]}
        feedback_grade_ids = {f["grade_id"] for f in data["feedbacks"]}
        assert grade_ids == feedback_grade_ids, \
            f"{len(grade_ids - feedback_grade_ids)} grades missing feedback"
