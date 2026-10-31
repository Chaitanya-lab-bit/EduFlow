"""
tests/test_reproducibility.py

Reproducibility verification: generate the dataset twice with the same seed and
confirm identical row counts and SHA-256 checksums of every table's CSV.
"""
import sys
import hashlib
import csv
import io
import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_generation.main import generate_dataset
from data_generation.config import STARTER_CONFIG


def dataset_checksums(data: dict) -> dict[str, str]:
    """Compute SHA-256 digest of each table's records serialised to CSV string."""
    checksums = {}
    for table_key, records in data.items():
        if not records:
            checksums[table_key] = hashlib.sha256(b"").hexdigest()
            continue
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
        raw = buf.getvalue().encode("utf-8")
        checksums[table_key] = hashlib.sha256(raw).hexdigest()
    return checksums


@pytest.fixture(scope="module")
def two_runs():
    """Generate the starter dataset twice and return both datasets + checksums."""
    data_a, anomalies_a, report_a = generate_dataset(STARTER_CONFIG)
    data_b, anomalies_b, report_b = generate_dataset(STARTER_CONFIG)
    checksums_a = dataset_checksums(data_a)
    checksums_b = dataset_checksums(data_b)
    return data_a, data_b, anomalies_a, anomalies_b, checksums_a, checksums_b


class TestRowCountReproducibility:
    """Row counts must be identical across two runs with the same seed."""

    def test_courses_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["courses"]) == len(b["courses"])

    def test_learners_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["learners"]) == len(b["learners"])

    def test_enrollments_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["enrollments"]) == len(b["enrollments"])

    def test_assignments_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["assignments"]) == len(b["assignments"])

    def test_rubrics_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["rubrics"]) == len(b["rubrics"])

    def test_rubric_criteria_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["rubric_criteria"]) == len(b["rubric_criteria"])

    def test_submissions_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["submissions"]) == len(b["submissions"])

    def test_artifacts_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["submission_artifacts"]) == len(b["submission_artifacts"])

    def test_status_histories_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["submission_status_histories"]) == len(b["submission_status_histories"])

    def test_grades_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["grades"]) == len(b["grades"])

    def test_grade_criterion_scores_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["grade_criterion_scores"]) == len(b["grade_criterion_scores"])

    def test_feedbacks_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["feedbacks"]) == len(b["feedbacks"])

    def test_resubmissions_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["resubmissions"]) == len(b["resubmissions"])

    def test_appeals_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["appeals"]) == len(b["appeals"])

    def test_audit_logs_count_identical(self, two_runs):
        a, b, *_ = two_runs
        assert len(a["audit_logs"]) == len(b["audit_logs"])

    def test_anomalies_count_identical(self, two_runs):
        _, _, anoms_a, anoms_b, *_ = two_runs
        assert len(anoms_a) == len(anoms_b)


class TestChecksumReproducibility:
    """SHA-256 checksums of serialised CSV must be identical across two runs."""

    def _check_table(self, two_runs, table_key: str):
        *_, checksums_a, checksums_b = two_runs
        assert table_key in checksums_a, f"Table {table_key} not in run A checksums"
        assert table_key in checksums_b, f"Table {table_key} not in run B checksums"
        assert checksums_a[table_key] == checksums_b[table_key], \
            f"Checksum mismatch for {table_key}:\n  Run A: {checksums_a[table_key]}\n  Run B: {checksums_b[table_key]}"

    def test_courses_checksum(self, two_runs):
        self._check_table(two_runs, "courses")

    def test_learners_checksum(self, two_runs):
        self._check_table(two_runs, "learners")

    def test_enrollments_checksum(self, two_runs):
        self._check_table(two_runs, "enrollments")

    def test_assignments_checksum(self, two_runs):
        self._check_table(two_runs, "assignments")

    def test_rubrics_checksum(self, two_runs):
        self._check_table(two_runs, "rubrics")

    def test_rubric_criteria_checksum(self, two_runs):
        self._check_table(two_runs, "rubric_criteria")

    def test_submissions_checksum(self, two_runs):
        self._check_table(two_runs, "submissions")

    def test_grades_checksum(self, two_runs):
        self._check_table(two_runs, "grades")

    def test_grade_criterion_scores_checksum(self, two_runs):
        self._check_table(two_runs, "grade_criterion_scores")

    def test_feedbacks_checksum(self, two_runs):
        self._check_table(two_runs, "feedbacks")

    def test_resubmissions_checksum(self, two_runs):
        self._check_table(two_runs, "resubmissions")

    def test_appeals_checksum(self, two_runs):
        self._check_table(two_runs, "appeals")

    def test_audit_logs_checksum(self, two_runs):
        self._check_table(two_runs, "audit_logs")


class TestChecksumReport:
    """Generate and print the final checksum manifest for documentation."""

    def test_print_checksum_manifest(self, two_runs, capsys):
        *_, checksums_a, checksums_b = two_runs
        print("\n" + "=" * 70)
        print("REPRODUCIBILITY CHECKSUM REPORT (Seed: 20261022)")
        print("=" * 70)
        all_match = True
        for table, sha in checksums_a.items():
            match = "✓" if sha == checksums_b[table] else "✗"
            if sha != checksums_b[table]:
                all_match = False
            print(f"  {match} {table:38s} {sha[:20]}...")
        print("=" * 70)
        print(f"  Result: {'ALL IDENTICAL ✓' if all_match else 'MISMATCHES FOUND ✗'}")
        print("=" * 70)
        assert all_match, "Checksum mismatches detected across two runs with seed 20261022"
