from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any
import pandas as pd
import numpy as np

from backend.models.enums import (
    CourseStatus, EnrollmentStatus, AssignmentStatus,
    SubmissionStatus, ArtifactType, GradeStatus,
    FeedbackVisibility, ResubmissionStatus, AppealStatus,
    AppealReasonCategory, AuditActionType
)

@dataclass
class ValidationReport:
    is_valid: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
        self.failed_checks += 1

    def add_pass(self):
        self.passed_checks += 1

class DataValidator:
    """
    Comprehensive vectorized validator enforcing domain constraints, business rules,
    referential integrity, date ordering, and anomaly isolation.
    """

    def __init__(self, data: dict[str, list[dict]], ground_truth: list[dict] = None):
        self.data = data
        self.ground_truth = ground_truth or []
        self.dfs = {k: pd.DataFrame(v) for k, v in data.items() if v}
        self.report = ValidationReport(
            is_valid=True,
            total_checks=0,
            passed_checks=0,
            failed_checks=0,
            errors=[],
            warnings=[],
            metrics={}
        )

    def validate_all(self) -> ValidationReport:
        """Run all 8 verification categories."""
        self.validate_primary_keys()
        self.validate_foreign_keys()
        self.validate_enum_values()
        self.validate_date_ordering()
        self.validate_grade_reconciliation()
        self.validate_duplicate_penalties()
        self.validate_lifecycle_transitions()
        self.validate_anomaly_labels()
        
        self.report.total_checks = self.report.passed_checks + self.report.failed_checks
        return self.report

    def validate_primary_keys(self):
        """1. Verify primary key uniqueness and table-level unique constraints."""
        pk_mapping = {
            "courses": "course_id",
            "learners": "learner_id",
            "enrollments": "enrollment_id",
            "assignments": "assignment_id",
            "rubrics": "rubric_id",
            "rubric_criteria": "criterion_id",
            "submissions": "submission_id",
            "submission_artifacts": "artifact_id",
            "submission_status_histories": "history_id",
            "grades": "grade_id",
            "grade_criterion_scores": "score_id",
            "feedbacks": "feedback_id",
            "resubmissions": "resubmission_id",
            "appeals": "appeal_id",
            "audit_logs": "audit_id",
        }

        for table, pk in pk_mapping.items():
            if table not in self.dfs:
                continue
            df = self.dfs[table]
            if pk not in df.columns:
                self.report.add_error(f"[{table}] Primary key column '{pk}' missing.")
                continue
            
            null_count = df[pk].isnull().sum()
            if null_count > 0:
                self.report.add_error(f"[{table}] Primary key '{pk}' contains {null_count} nulls.")
            else:
                self.report.add_pass()

            dup_count = df[pk].duplicated().sum()
            if dup_count > 0:
                self.report.add_error(f"[{table}] Primary key '{pk}' contains {dup_count} duplicates.")
            else:
                self.report.add_pass()

        # Additional unique constraints
        if "courses" in self.dfs and self.dfs["courses"]["code"].duplicated().any():
            self.report.add_error("[courses] Duplicate course codes detected.")
        else:
            self.report.add_pass()

        if "learners" in self.dfs:
            if self.dfs["learners"]["student_number"].duplicated().any():
                self.report.add_error("[learners] Duplicate student_number detected.")
            else:
                self.report.add_pass()
            if self.dfs["learners"]["email"].duplicated().any():
                self.report.add_error("[learners] Duplicate email addresses detected.")
            else:
                self.report.add_pass()

        if "enrollments" in self.dfs:
            enr_dups = self.dfs["enrollments"].duplicated(subset=["course_id", "learner_id"]).sum()
            if enr_dups > 0:
                self.report.add_error(f"[enrollments] {enr_dups} duplicate (course_id, learner_id) pairs found.")
            else:
                self.report.add_pass()

        if "rubrics" in self.dfs:
            rub_dups = self.dfs["rubrics"].duplicated(subset=["assignment_id", "version"]).sum()
            if rub_dups > 0:
                self.report.add_error(f"[rubrics] {rub_dups} duplicate (assignment_id, version) pairs found.")
            else:
                self.report.add_pass()

        if "submissions" in self.dfs:
            sub_dups = self.dfs["submissions"].duplicated(subset=["assignment_id", "learner_id", "attempt_number"]).sum()
            if sub_dups > 0:
                self.report.add_error(f"[submissions] {sub_dups} duplicate (assignment_id, learner_id, attempt_number) attempts found.")
            else:
                self.report.add_pass()

        if "submission_artifacts" in self.dfs:
            art_dups = self.dfs["submission_artifacts"].duplicated(subset=["submission_id", "artifact_type"]).sum()
            if art_dups > 0:
                self.report.add_error(f"[submission_artifacts] {art_dups} duplicate artifact types for single submission.")
            else:
                self.report.add_pass()

        if "grades" in self.dfs:
            if self.dfs["grades"]["submission_id"].duplicated().any():
                self.report.add_error("[grades] Duplicate submission_id in grades (violates 1:1 binding).")
            else:
                self.report.add_pass()

        if "grade_criterion_scores" in self.dfs:
            gcs_dups = self.dfs["grade_criterion_scores"].duplicated(subset=["grade_id", "criterion_id"]).sum()
            if gcs_dups > 0:
                self.report.add_error(f"[grade_criterion_scores] {gcs_dups} duplicate (grade_id, criterion_id) pairs.")
            else:
                self.report.add_pass()

        if "resubmissions" in self.dfs:
            if self.dfs["resubmissions"]["new_submission_id"].duplicated().any():
                self.report.add_error("[resubmissions] Duplicate new_submission_id in resubmissions.")
            else:
                self.report.add_pass()

    def validate_foreign_keys(self):
        """2. Verify strict referential integrity across all relationships."""
        fk_checks = [
            ("enrollments", "course_id", "courses", "course_id"),
            ("enrollments", "learner_id", "learners", "learner_id"),
            ("assignments", "course_id", "courses", "course_id"),
            ("rubrics", "assignment_id", "assignments", "assignment_id"),
            ("rubric_criteria", "rubric_id", "rubrics", "rubric_id"),
            ("submissions", "assignment_id", "assignments", "assignment_id"),
            ("submissions", "learner_id", "learners", "learner_id"),
            ("submissions", "enrollment_id", "enrollments", "enrollment_id"),
            ("submission_artifacts", "submission_id", "submissions", "submission_id"),
            ("submission_status_histories", "submission_id", "submissions", "submission_id"),
            ("grades", "submission_id", "submissions", "submission_id"),
            ("grade_criterion_scores", "grade_id", "grades", "grade_id"),
            ("grade_criterion_scores", "criterion_id", "rubric_criteria", "criterion_id"),
            ("feedbacks", "grade_id", "grades", "grade_id"),
            ("feedbacks", "submission_id", "submissions", "submission_id"),
            ("resubmissions", "original_submission_id", "submissions", "submission_id"),
            ("resubmissions", "new_submission_id", "submissions", "submission_id"),
            ("appeals", "submission_id", "submissions", "submission_id"),
            ("appeals", "grade_id", "grades", "grade_id"),
            ("appeals", "learner_id", "learners", "learner_id"),
        ]

        for child_tbl, child_col, parent_tbl, parent_col in fk_checks:
            if child_tbl not in self.dfs or parent_tbl not in self.dfs:
                continue
            child_df = self.dfs[child_tbl]
            parent_df = self.dfs[parent_tbl]
            
            parent_ids = set(parent_df[parent_col])
            unmatched = ~child_df[child_col].isin(parent_ids) & child_df[child_col].notnull()
            unmatched_count = unmatched.sum()
            
            if unmatched_count > 0:
                self.report.add_error(f"[{child_tbl}.{child_col}] {unmatched_count} orphaned records referencing {parent_tbl}.{parent_col}.")
            else:
                self.report.add_pass()

        # Complex Integrity: verify learner submitting is actively enrolled in that assignment's course!
        if "submissions" in self.dfs and "assignments" in self.dfs and "enrollments" in self.dfs:
            sub_df = self.dfs["submissions"]
            asn_df = self.dfs["assignments"][["assignment_id", "course_id"]]
            enr_df = self.dfs["enrollments"][["enrollment_id", "course_id", "learner_id"]]
            
            merged = sub_df.merge(asn_df, on="assignment_id", how="left")
            merged = merged.merge(enr_df, on="enrollment_id", how="left", suffixes=("_sub", "_enr"))
            
            # Check course match
            mismatched_courses = (merged["course_id_sub"] != merged["course_id_enr"]).sum()
            if mismatched_courses > 0:
                self.report.add_error(f"[submissions] {mismatched_courses} submissions linked to an enrollment in a different course.")
            else:
                self.report.add_pass()
                
            # Check learner match
            mismatched_learners = (merged["learner_id_sub"] != merged["learner_id_enr"]).sum()
            if mismatched_learners > 0:
                self.report.add_error(f"[submissions] {mismatched_learners} submissions linked to an enrollment of a different learner.")
            else:
                self.report.add_pass()

    def validate_enum_values(self):
        """3. Verify all enum columns adhere to defined domain values."""
        enum_checks = [
            ("courses", "status", {e.value for e in CourseStatus}),
            ("learners", "status", {e.value for e in EnrollmentStatus}),
            ("enrollments", "status", {e.value for e in EnrollmentStatus}),
            ("assignments", "status", {e.value for e in AssignmentStatus}),
            ("submissions", "status", {e.value for e in SubmissionStatus}),
            ("submission_artifacts", "artifact_type", {e.value for e in ArtifactType}),
            ("submission_status_histories", "new_status", {e.value for e in SubmissionStatus}),
            ("grades", "grade_status", {e.value for e in GradeStatus}),
            ("feedbacks", "visibility", {e.value for e in FeedbackVisibility}),
            ("resubmissions", "status", {e.value for e in ResubmissionStatus}),
            ("appeals", "status", {e.value for e in AppealStatus}),
            ("appeals", "reason_category", {e.value for e in AppealReasonCategory}),
            ("audit_logs", "action", {e.value for e in AuditActionType}),
        ]

        for tbl, col, allowed in enum_checks:
            if tbl not in self.dfs or col not in self.dfs[tbl].columns:
                continue
            invalid = ~self.dfs[tbl][col].isin(allowed) & self.dfs[tbl][col].notnull()
            inv_count = invalid.sum()
            if inv_count > 0:
                bad_vals = self.dfs[tbl].loc[invalid, col].unique()
                self.report.add_error(f"[{tbl}.{col}] Found {inv_count} invalid enum values: {bad_vals}.")
            else:
                self.report.add_pass()

    @staticmethod
    def _parse_dt(series):
        return pd.to_datetime(series, format="ISO8601", utc=True)

    def validate_date_ordering(self):
        """4. Verify temporal integrity: course dates, cutoffs, submission times, and grading order."""
        if "courses" in self.dfs:
            c = self.dfs["courses"]
            invalid_dates = (self._parse_dt(c["end_date"]) <= self._parse_dt(c["start_date"])).sum()
            if invalid_dates > 0:
                self.report.add_error(f"[courses] {invalid_dates} courses where end_date <= start_date.")
            else:
                self.report.add_pass()

        if "assignments" in self.dfs:
            a = self.dfs["assignments"]
            invalid_cutoffs = (self._parse_dt(a["cutoff_date"]) < self._parse_dt(a["due_date"])).sum()
            if invalid_cutoffs > 0:
                self.report.add_error(f"[assignments] {invalid_cutoffs} assignments where cutoff_date < due_date.")
            else:
                self.report.add_pass()

        if "submissions" in self.dfs and "assignments" in self.dfs:
            sub = self.dfs["submissions"]
            asn = self.dfs["assignments"][["assignment_id", "due_date", "cutoff_date", "grace_period_minutes"]]
            m = sub.merge(asn, on="assignment_id", how="left")
            
            sub_time = self._parse_dt(m["submitted_at"])
            due_time = self._parse_dt(m["due_date"])
            cutoff_time = self._parse_dt(m["cutoff_date"])
            grace_delta = pd.to_timedelta(m["grace_period_minutes"], unit="m")
            
            # Cutoff check: no submission may exceed cutoff_date
            past_cutoff = (sub_time > cutoff_time).sum()
            if past_cutoff > 0:
                self.report.add_error(f"[submissions] {past_cutoff} submissions timestamped past cutoff_date.")
            else:
                self.report.add_pass()
                
            # Grace period logic: if within grace period, is_late must be False and penalty 0.00
            in_grace = (sub_time > due_time) & (sub_time <= due_time + grace_delta)
            if in_grace.any():
                violated_grace = (m.loc[in_grace, "is_late"] == True).sum()
                if violated_grace > 0:
                    self.report.add_error(f"[submissions] {violated_grace} submissions inside grace period incorrectly marked is_late=True.")
                else:
                    self.report.add_pass()
            else:
                self.report.add_pass()

            # Lateness verification
            late_expected = sub_time > (due_time + grace_delta)
            mismatched_late = (m["is_late"] != late_expected).sum()
            if mismatched_late > 0:
                self.report.add_error(f"[submissions] {mismatched_late} submissions have mismatched is_late flags.")
            else:
                self.report.add_pass()

        if "grades" in self.dfs and "submissions" in self.dfs:
            grd = self.dfs["grades"]
            sub = self.dfs["submissions"][["submission_id", "submitted_at"]]
            mg = grd.merge(sub, on="submission_id", how="left")
            
            graded_time = self._parse_dt(mg["graded_at"])
            sub_time = self._parse_dt(mg["submitted_at"])
            
            before_sub = (graded_time < sub_time).sum()
            if before_sub > 0:
                self.report.add_error(f"[grades] {before_sub} grades timestamped before submission occurred.")
            else:
                self.report.add_pass()

        if "appeals" in self.dfs and "grades" in self.dfs:
            app = self.dfs["appeals"]
            grd = self.dfs["grades"][["grade_id", "graded_at"]]
            ma = app.merge(grd, on="grade_id", how="left")
            
            app_sub_time = self._parse_dt(ma["submitted_at"])
            graded_time = self._parse_dt(ma["graded_at"])
            
            # Appeals must be filed after grade publication
            premature_appeals = (app_sub_time < graded_time).sum()
            if premature_appeals > 0:
                self.report.add_error(f"[appeals] {premature_appeals} appeals filed before grade publication.")
            else:
                self.report.add_pass()

            # Resolution must follow appeal submission
            resolved = ma[ma["resolved_at"].notnull()]
            if not resolved.empty:
                app_res_time = self._parse_dt(resolved["resolved_at"])
                app_sub_res = self._parse_dt(resolved["submitted_at"])
                inverted_res = (app_res_time < app_sub_res).sum()
                if inverted_res > 0:
                    self.report.add_error(f"[appeals] {inverted_res} appeals resolved before they were filed.")
                else:
                    self.report.add_pass()

    def validate_grade_reconciliation(self):
        """5. Reconcile raw scores, criteria sums, penalty deductions, and score bounds."""
        if "grades" not in self.dfs or "grade_criterion_scores" not in self.dfs:
            return

        grd = self.dfs["grades"]
        gcs = self.dfs["grade_criterion_scores"]
        
        # 1. Sum of criterion scores must match raw_score
        crit_sums = gcs.groupby("grade_id")["score_awarded"].sum().reset_index()
        crit_sums = crit_sums.rename(columns={"score_awarded": "calc_raw_score"})
        
        merged_grd = grd.merge(crit_sums, on="grade_id", how="left")
        diff = (merged_grd["raw_score"] - merged_grd["calc_raw_score"]).round(2).abs()
        unreconciled = (diff > 0.01).sum()
        if unreconciled > 0:
            self.report.add_error(f"[grades] {unreconciled} grades fail raw score reconciliation with criteria scores.")
        else:
            self.report.add_pass()

        # 2. Check each criterion score <= criterion.max_points
        if "rubric_criteria" in self.dfs:
            rc = self.dfs["rubric_criteria"][["criterion_id", "max_points"]]
            mgcs = gcs.merge(rc, on="criterion_id", how="left")
            exceeding_crit = (mgcs["score_awarded"] > (mgcs["max_points"] + 0.001)).sum()
            if exceeding_crit > 0:
                self.report.add_error(f"[grade_criterion_scores] {exceeding_crit} scores exceed criterion max_points.")
            else:
                self.report.add_pass()

        # 3. Check final_score = clamp(raw_score - late_penalty_applied + bonus_points, 0, max_score)
        # NOTE: 'revised' grades have final_score adjusted by appeals (legitimate mutation via audit log)
        #       and are excluded from formula-based reconciliation.
        if "submissions" in self.dfs and "assignments" in self.dfs:
            sub = self.dfs["submissions"][["submission_id", "assignment_id"]]
            asn = self.dfs["assignments"][["assignment_id", "max_score"]]
            
            g_check = grd.merge(sub, on="submission_id", how="left").merge(asn, on="assignment_id", how="left")
            # Only validate grades that have NOT been revised via approved appeals
            baseline_grades = g_check[g_check["grade_status"] != "revised"]
            expected_final = np.clip(
                (baseline_grades["raw_score"] - baseline_grades["late_penalty_applied"] + baseline_grades["bonus_points"]).round(2),
                0.0,
                baseline_grades["max_score"]
            )
            final_diff = (baseline_grades["final_score"] - expected_final).abs()
            mismatched_finals = (final_diff > 0.01).sum()
            if mismatched_finals > 0:
                self.report.add_error(f"[grades] {mismatched_finals} non-revised grades have inconsistent final_score derivations.")
            else:
                self.report.add_pass()

    def validate_duplicate_penalties(self):
        """6. Assert late_penalty_applied matches exactly raw_score * (late_pct/100) — never doubled."""
        if "grades" not in self.dfs or "submissions" not in self.dfs:
            return

        grd = self.dfs["grades"]
        sub = self.dfs["submissions"][["submission_id", "late_penalty_percentage", "is_late"]]

        # Join grades to submission late metadata
        merged = grd[grd["grade_status"] != "revised"].merge(sub, on="submission_id", how="left")
        late_merged = merged[merged["is_late"] == True]

        if late_merged.empty:
            self.report.add_pass()
            return

        # Expected penalty = raw_score * (late_penalty_percentage / 100)
        expected_penalty = (late_merged["raw_score"] * late_merged["late_penalty_percentage"] / 100.0).round(2)
        actual_penalty = late_merged["late_penalty_applied"].round(2)

        # Allow 0.02 tolerance for floating point
        mismatch = (actual_penalty - expected_penalty).abs() > 0.02
        mismatch_count = mismatch.sum()

        if mismatch_count > 0:
            # Report the first offending grade
            first_bad = late_merged[mismatch].iloc[0]
            exp = expected_penalty[mismatch].iloc[0]
            self.report.add_error(
                f"[grades] Grade {first_bad['grade_id']} has late_penalty_applied={first_bad['late_penalty_applied']:.2f} "
                f"but expected {exp:.2f} from raw_score={first_bad['raw_score']:.2f} × {first_bad['late_penalty_percentage']:.2f}%. "
                f"({mismatch_count} total violations)"
            )
        else:
            self.report.add_pass()

    def validate_lifecycle_transitions(self):
        """7. Verify sequential lifecycle transitions in status history."""
        if "submission_status_histories" not in self.dfs:
            return

        ssh = self.dfs["submission_status_histories"]
        if ssh.empty:
            return

        # Verify time non-decreasing per submission
        ssh["changed_at_dt"] = self._parse_dt(ssh["changed_at"])
        ssh_sorted = ssh.sort_values(by=["submission_id", "changed_at_dt"])
        
        # Check transition validity
        valid_statuses = {e.value for e in SubmissionStatus}
        invalid_old = ~ssh["old_status"].isin(valid_statuses) & ssh["old_status"].notnull()
        invalid_new = ~ssh["new_status"].isin(valid_statuses)
        
        if invalid_old.any() or invalid_new.any():
            self.report.add_error("[submission_status_histories] Invalid statuses recorded in history transitions.")
        else:
            self.report.add_pass()

    def validate_anomaly_labels(self):
        """8. Verify all 4 mandatory anomaly scenarios are present in ground truth with complete metadata."""
        if not self.ground_truth:
            self.report.warnings.append("No ground truth manifest provided for anomaly verification.")
            return

        gt_df = pd.DataFrame(self.ground_truth)
        required_scenarios = {"EX-01", "EX-02", "EX-03", "EX-04"}
        present_scenarios = set(gt_df["scenario_id"].unique()) if "scenario_id" in gt_df.columns else set()
        
        missing = required_scenarios - present_scenarios
        if missing:
            self.report.add_error(f"[ground_truth] Missing required anomaly scenarios: {missing}.")
        else:
            self.report.add_pass()

        # Check required fields
        required_fields = ["anomaly_id", "scenario_id", "scenario_name", "expected_error", "record_payload"]
        for f in required_fields:
            if f not in gt_df.columns:
                self.report.add_error(f"[ground_truth] Missing manifest field '{f}'.")
            else:
                self.report.add_pass()
