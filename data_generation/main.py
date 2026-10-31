import argparse
import sys
import time
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_generation.config import DatasetConfig, STARTER_CONFIG, FULL_CONFIG, CONFIG_PROFILES
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
from data_generation.validators.data_validator import DataValidator, ValidationReport
from data_generation.exports.exporter import DataExporter

def generate_dataset(config: DatasetConfig) -> tuple[dict[str, list[dict]], list[dict], ValidationReport]:
    """
    Orchestrate full synthetic data generation pipeline deterministically.
    Returns:
        data: dictionary mapping table names to list of record dicts
        anomalies: list of ground truth anomaly descriptors
        report: validation outcome report
    """
    seed = config.seed
    
    # 1. Master Data (Courses & Learners)
    courses = generate_courses(config.num_courses, seed)
    learners, competency_map = generate_learners(config.num_learners, seed)
    
    # 2. Enrollments
    enrollments, enrollment_map = generate_enrollments(
        courses,
        learners,
        config.min_enrollments_per_learner,
        config.max_enrollments_per_learner,
        seed
    )
    
    # 3. Assignments, Rubrics, and Criteria
    assignments, rubrics, criteria = generate_assignments_and_rubrics(
        courses,
        config.num_assignments,
        config.criteria_per_rubric,
        config.additional_rubric_versions,
        seed
    )
    
    # 4. Initial Submissions & Lifecycle Histories
    submissions, status_histories = generate_submissions(
        assignments,
        enrollments,
        config.num_submissions,
        seed
    )
    
    # 5. Submission Artifacts
    artifacts = generate_artifacts(submissions, assignments, seed)
    
    # 6. Evaluation & Grading
    grades, criteria_scores, ssh_grades, ssh_counter = generate_grades(
        submissions,
        assignments,
        rubrics,
        criteria,
        competency_map,
        config.grade_rate,
        seed,
        ssh_counter_start=len(status_histories) + 1
    )
    status_histories.extend(ssh_grades)
    
    # 7. Mentoring & Qualitative Feedback
    feedback = generate_feedback(grades, seed)
    
    # 8. Resubmissions (Attempt 2 workflows)
    (
        resubs,
        new_subs,
        new_arts,
        new_grds,
        new_crit_scs,
        new_fbk,
        new_ssh,
        ssh_counter
    ) = generate_resubmissions(
        submissions,
        assignments,
        rubrics,
        criteria,
        grades,
        config.resubmission_rate,
        seed,
        ssh_counter_start=ssh_counter
    )
    submissions.extend(new_subs)
    artifacts.extend(new_arts)
    grades.extend(new_grds)
    criteria_scores.extend(new_crit_scs)
    feedback.extend(new_fbk)
    status_histories.extend(new_ssh)
    
    # 9. Academic Appeals & Immutable Audit Logging
    appeals, audit_logs, audit_counter = generate_appeals(
        grades,
        submissions,
        config.appeal_rate,
        seed
    )
    
    # 10. Deliberate Anomaly Scenarios (Separated in ground_truth dataset)
    anomalies, anomaly_datasets = generate_anomalies(
        courses,
        learners,
        enrollments,
        assignments,
        rubrics,
        criteria,
        submissions,
        grades,
        seed
    )
    
    dataset = {
        "courses": courses,
        "learners": learners,
        "enrollments": enrollments,
        "assignments": assignments,
        "rubrics": rubrics,
        "rubric_criteria": criteria,
        "submissions": submissions,
        "submission_artifacts": artifacts,
        "submission_status_histories": status_histories,
        "grades": grades,
        "grade_criterion_scores": criteria_scores,
        "feedbacks": feedback,
        "resubmissions": resubs,
        "appeals": appeals,
        "audit_logs": audit_logs,
    }
    
    # Validate entire dataset
    validator = DataValidator(dataset, anomalies)
    report = validator.validate_all()
    
    return dataset, anomalies, report

def run_pipeline(profile_name: str = "starter", export: bool = True):
    """Run generation, validation, and export for specified profile."""
    config = CONFIG_PROFILES.get(profile_name, STARTER_CONFIG)
    print(f"==================================================")
    print(f"Starting EduFlow Synthetic Data Generation Engine")
    print(f"Profile: {config.profile_name.upper()} | Seed: {config.seed}")
    print(f"==================================================")
    
    t0 = time.time()
    dataset, anomalies, report = generate_dataset(config)
    gen_time = time.time() - t0
    
    print(f"\n[Generation Complete in {gen_time:.2f}s]")
    print(f"--------------------------------------------------")
    print(f"Row Counts Summary:")
    for k, v in dataset.items():
        print(f"  * {k:28s}: {len(v):,d}")
    print(f"  * {'ground_truth_anomalies':28s}: {len(anomalies):,d}")
    print(f"--------------------------------------------------")
    
    print(f"\n[Validation Results]")
    print(f"  Total Checks  : {report.total_checks}")
    print(f"  Passed Checks : {report.passed_checks}")
    print(f"  Failed Checks : {report.failed_checks}")
    print(f"  Status        : {'PASSED (100% VALID)' if report.is_valid else 'FAILED'}")
    
    if report.errors:
        print(f"\nValidation Errors ({len(report.errors)}):")
        for err in report.errors:
            print(f"  - [FAIL] {err}")
    if report.warnings:
        print(f"\nValidation Warnings ({len(report.warnings)}):")
        for warn in report.warnings:
            print(f"  - [WARN] {warn}")
            
    if export:
        print(f"\n[Exporting Data]")
        exporter = DataExporter(config.exports_dir)
        exported = exporter.export_all(dataset, anomalies)
        print(f"  Exports directory: {config.exports_dir}")
        print(f"  SQL Seed File    : {exported['sql']}")
        print(f"  CSV Tables       : {len([k for k in exported if k.startswith('csv_')])} files")
        print(f"  JSON Tables      : {len([k for k in exported if k.startswith('json_')])} files")
        print(f"  Ground Truth     : {exported.get('gt_csv')}")
        
    print(f"\nPipeline finished successfully in {time.time() - t0:.2f}s.")
    return dataset, anomalies, report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EduFlow Synthetic Data Generation Engine")
    parser.add_argument("--profile", choices=["starter", "full"], default="starter", help="Dataset configuration profile")
    parser.add_argument("--no-export", action="store_true", help="Skip writing export files")
    parser.add_argument("--all", action="store_true", help="Generate both starter and full datasets sequentially")
    
    args = parser.parse_args()
    
    if args.all:
        print("\n>>> Generating Starter Dataset Profile <<<")
        run_pipeline("starter", export=not args.no_export)
        print("\n>>> Generating Full Dataset Profile <<<")
        run_pipeline("full", export=not args.no_export)
    else:
        run_pipeline(args.profile, export=not args.no_export)
