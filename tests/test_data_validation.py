"""
tests/test_data_validation.py

Tests that the DataValidator correctly enforces all 8 validation categories
against both clean and intentionally corrupt datasets.
"""
import sys
from pathlib import Path
import pytest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_generation.main import generate_dataset
from data_generation.config import STARTER_CONFIG
from data_generation.validators.data_validator import DataValidator


@pytest.fixture(scope="module")
def starter_data():
    data, anomalies, report = generate_dataset(STARTER_CONFIG)
    return data, anomalies, report


class TestValidationPassesOnCleanDataset:
    """The starter dataset should produce 0 validation errors."""

    def test_validation_passes_completely(self, starter_data):
        data, anomalies, report = starter_data
        assert report.is_valid, f"Validation failed with errors: {report.errors}"

    def test_zero_errors(self, starter_data):
        _, _, report = starter_data
        assert report.failed_checks == 0, f"Unexpected failures: {report.errors}"

    def test_check_count_nonzero(self, starter_data):
        _, _, report = starter_data
        assert report.total_checks > 0

    def test_all_8_categories_ran(self, starter_data):
        _, _, report = starter_data
        # Total checks >= 40 indicates all categories ran substantively
        assert report.total_checks >= 40


class TestPrimaryKeyValidation:
    def test_detects_duplicate_course_id(self, starter_data):
        data, anomalies, _ = starter_data
        # Inject a duplicate
        corrupt = dict(data)
        dup_course = dict(data["courses"][0])
        corrupt["courses"] = data["courses"] + [dup_course]
        v = DataValidator(corrupt)
        v.validate_primary_keys()
        assert v.report.failed_checks > 0, "Expected PK duplicate detection to fail"

    def test_detects_duplicate_enrollment_pair(self, starter_data):
        data, _, _ = starter_data
        corrupt = dict(data)
        dup_enr = dict(data["enrollments"][0])
        corrupt["enrollments"] = data["enrollments"] + [dup_enr]
        v = DataValidator(corrupt)
        v.validate_primary_keys()
        assert v.report.failed_checks > 0

    def test_detects_duplicate_grade_submission_binding(self, starter_data):
        data, _, _ = starter_data
        corrupt = dict(data)
        dup_grade = dict(data["grades"][0])
        dup_grade["grade_id"] = "GRD-FAKE-999"
        corrupt["grades"] = data["grades"] + [dup_grade]
        v = DataValidator(corrupt)
        v.validate_primary_keys()
        assert v.report.failed_checks > 0, "Duplicate submission_id in grades should be detected"


class TestForeignKeyValidation:
    def test_detects_orphaned_submission(self, starter_data):
        data, _, _ = starter_data
        corrupt = dict(data)
        orphan_sub = dict(data["submissions"][0])
        orphan_sub["submission_id"] = "SUB-ORPHAN-001"
        orphan_sub["enrollment_id"] = "ENR-2026-999999"  # non-existent
        corrupt["submissions"] = data["submissions"] + [orphan_sub]
        v = DataValidator(corrupt)
        v.validate_foreign_keys()
        assert v.report.failed_checks > 0, "Orphaned enrollment_id should be detected"

    def test_detects_orphaned_grade_criterion_score(self, starter_data):
        data, _, _ = starter_data
        corrupt = dict(data)
        orphan_gcs = dict(data["grade_criterion_scores"][0])
        orphan_gcs["score_id"] = "GCS-ORPHAN-001"
        orphan_gcs["grade_id"] = "GRD-NONEXISTENT"
        corrupt["grade_criterion_scores"] = data["grade_criterion_scores"] + [orphan_gcs]
        v = DataValidator(corrupt)
        v.validate_foreign_keys()
        assert v.report.failed_checks > 0

    def test_clean_dataset_has_no_fk_errors(self, starter_data):
        data, _, _ = starter_data
        v = DataValidator(data)
        v.validate_foreign_keys()
        assert v.report.failed_checks == 0


class TestEnumValidation:
    def test_detects_invalid_submission_status(self, starter_data):
        data, _, _ = starter_data
        corrupt = dict(data)
        bad_sub = dict(data["submissions"][0])
        bad_sub["submission_id"] = "SUB-ENUM-TEST"
        bad_sub["status"] = "HACKED_STATUS"
        corrupt["submissions"] = data["submissions"] + [bad_sub]
        v = DataValidator(corrupt)
        v.validate_enum_values()
        assert v.report.failed_checks > 0, "Invalid enum should be detected"

    def test_detects_invalid_grade_status(self, starter_data):
        data, _, _ = starter_data
        corrupt = dict(data)
        bad_grd = dict(data["grades"][0])
        bad_grd["grade_id"] = "GRD-ENUM-TEST"
        bad_grd["grade_status"] = "NOT_A_STATUS"
        corrupt["grades"] = data["grades"] + [bad_grd]
        v = DataValidator(corrupt)
        v.validate_enum_values()
        assert v.report.failed_checks > 0

    def test_clean_dataset_has_no_enum_errors(self, starter_data):
        data, _, _ = starter_data
        v = DataValidator(data)
        v.validate_enum_values()
        assert v.report.failed_checks == 0


class TestDateOrderingValidation:
    def test_detects_submission_past_cutoff(self, starter_data):
        from datetime import datetime, timedelta, timezone
        data, _, _ = starter_data
        corrupt = dict(data)
        asn = data["assignments"][0]
        cutoff_time = datetime.fromisoformat(asn["cutoff_date"]) + timedelta(days=10)
        bad_sub = dict(data["submissions"][0])
        bad_sub["submission_id"] = "SUB-DATE-TEST"
        bad_sub["assignment_id"] = asn["assignment_id"]
        bad_sub["submitted_at"] = cutoff_time.isoformat()
        corrupt["submissions"] = data["submissions"] + [bad_sub]
        v = DataValidator(corrupt)
        v.validate_date_ordering()
        assert v.report.failed_checks > 0, "Past-cutoff submission should be detected"

    def test_detects_grade_before_submission(self, starter_data):
        from datetime import datetime, timedelta
        data, _, _ = starter_data
        if not data["grades"]:
            pytest.skip("No grades in dataset")
        corrupt = dict(data)
        bad_grade = dict(data["grades"][0])
        bad_grade["grade_id"] = "GRD-TIMETEST"
        # Set graded_at to 2 days before submission
        sub_time = datetime.fromisoformat(data["submissions"][0]["submitted_at"])
        bad_grade["submission_id"] = data["submissions"][0]["submission_id"]
        bad_grade["graded_at"] = (sub_time - timedelta(days=2)).isoformat()
        corrupt["grades"] = data["grades"] + [bad_grade]
        v = DataValidator(corrupt)
        v.validate_date_ordering()
        assert v.report.failed_checks > 0, "Grade before submission should be detected"


class TestGradeReconciliationValidation:
    def test_detects_criteria_sum_mismatch(self, starter_data):
        data, _, _ = starter_data
        if not data["grade_criterion_scores"]:
            pytest.skip("No criterion scores")
        corrupt = dict(data)
        # Add an extra criterion score to inflate the sum
        extra = dict(data["grade_criterion_scores"][0])
        extra["score_id"] = "GCS-INFLATE-001"
        extra["score_awarded"] = 999.0
        corrupt["grade_criterion_scores"] = data["grade_criterion_scores"] + [extra]
        v = DataValidator(corrupt)
        v.validate_grade_reconciliation()
        assert v.report.failed_checks > 0, "Criteria sum mismatch should be detected"

    def test_clean_grades_pass_reconciliation(self, starter_data):
        data, _, _ = starter_data
        v = DataValidator(data)
        v.validate_grade_reconciliation()
        assert v.report.failed_checks == 0


class TestDuplicatePenaltyValidation:
    def test_detects_doubled_penalty(self, starter_data):
        data, _, _ = starter_data
        # Find a late submission so the validator will inspect it
        late_subs = [s for s in data["submissions"] if s["is_late"]]
        if not late_subs:
            pytest.skip("No late submissions in starter dataset")
        ref_sub = late_subs[0]
        raw_score = 80.0
        pct = float(ref_sub["late_penalty_percentage"])
        single_penalty = round(raw_score * pct / 100.0, 2)
        # Apply the deduction *twice*: late_penalty_applied = 2 * correct_amount
        doubled_penalty = round(single_penalty * 2, 2)
        corrupt_grade = {
            "grade_id": f"GRD-{ref_sub['submission_id']}",
            "submission_id": ref_sub["submission_id"],
            "graded_by": "USR-INST-0001",
            "raw_score": raw_score,
            "late_penalty_applied": doubled_penalty,       # <-- doubled!
            "bonus_points": 0.0,
            "final_score": round(max(0.0, raw_score - doubled_penalty), 2),
            "is_final": True,
            "grade_status": "published",
            "graded_at": "2026-10-20T14:00:00+00:00",
            "created_at": "2026-10-20T14:00:00+00:00",
            "updated_at": "2026-10-20T14:00:00+00:00",
        }
        corrupt = dict(data)
        # Remove any existing grade for this submission, then inject the corrupt one
        corrupt["grades"] = [
            g for g in data["grades"] if g["submission_id"] != ref_sub["submission_id"]
        ] + [corrupt_grade]
        v = DataValidator(corrupt)
        v.validate_duplicate_penalties()
        assert v.report.failed_checks > 0, "Doubled late_penalty_applied should be detected by formula validator"

    def test_clean_grades_pass_penalty_check(self, starter_data):
        data, _, _ = starter_data
        v = DataValidator(data)
        v.validate_duplicate_penalties()
        assert v.report.failed_checks == 0


class TestAnomalyLabelValidation:
    def test_all_four_anomaly_scenarios_present(self, starter_data):
        data, anomalies, _ = starter_data
        v = DataValidator(data, anomalies)
        v.validate_anomaly_labels()
        assert v.report.failed_checks == 0

    def test_missing_anomaly_detected(self, starter_data):
        data, anomalies, _ = starter_data
        # Remove one scenario
        trimmed = [a for a in anomalies if a["scenario_id"] != "EX-04"]
        v = DataValidator(data, trimmed)
        v.validate_anomaly_labels()
        assert v.report.failed_checks > 0, "Missing EX-04 should be flagged"

    def test_empty_ground_truth_produces_warning(self, starter_data):
        data, _, _ = starter_data
        v = DataValidator(data, [])
        v.validate_anomaly_labels()
        assert len(v.report.warnings) > 0
