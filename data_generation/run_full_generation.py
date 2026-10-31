"""
data_generation/run_full_generation.py
Full-scale synthetic dataset generation, validation, export, and reproducibility check.

Usage:
    python data_generation/run_full_generation.py
"""
import sys
import time
import hashlib
import csv
import io
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import via explicit module paths (avoids generators/__init__.py circular re-import)
from data_generation.config import FULL_CONFIG
from data_generation.exports.exporter import DataExporter
# Delay the main import until after other modules are loaded to break circular chain
import importlib
_main_mod = importlib.import_module("data_generation.main")
generate_dataset = _main_mod.generate_dataset


def sha256_of_table(records: list[dict]) -> str:
    """Compute SHA-256 of a table's records serialised as CSV bytes."""
    if not records:
        return hashlib.sha256(b"").hexdigest()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    raw = buf.getvalue().encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def compute_checksums(dataset: dict) -> dict:
    return {table: sha256_of_table(records) for table, records in dataset.items()}


def print_section(title: str):
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)


def main():
    cfg = FULL_CONFIG

    print_section(f"FULL DATASET GENERATION  |  Profile: {cfg.profile_name.upper()}  |  Seed: {cfg.seed}")
    print(f"  Target volumes:")
    print(f"    Courses        : {cfg.num_courses:,}")
    print(f"    Learners       : {cfg.num_learners:,}")
    print(f"    Assignments    : {cfg.num_assignments:,}")
    print(f"    Submissions    : {cfg.num_submissions:,}")
    print(f"    Rubric versions: {cfg.additional_rubric_versions} additional per assignment slot")

    # ── 1. First generation run ─────────────────────────────────────────────
    print_section("RUN 1: Generating Dataset")
    t0 = time.time()
    dataset_a, anomalies_a, report_a = generate_dataset(cfg)
    gen1_time = time.time() - t0
    print(f"  Completed in {gen1_time:.2f}s")

    # ── 2. Record counts ────────────────────────────────────────────────────
    print_section("RECORD COUNTS (Run 1)")
    for table, records in dataset_a.items():
        print(f"  {table:40s}: {len(records):>8,}")
    print(f"  {'ground_truth_anomalies':40s}: {len(anomalies_a):>8,}")

    # ── 3. Validation results ───────────────────────────────────────────────
    print_section("VALIDATION RESULTS (Run 1)")
    print(f"  Total checks   : {report_a.total_checks}")
    print(f"  Passed checks  : {report_a.passed_checks}")
    print(f"  Failed checks  : {report_a.failed_checks}")
    status_str = "PASSED (100% VALID)" if report_a.is_valid else "FAILED"
    print(f"  Status         : {status_str}")
    if report_a.errors:
        print(f"\n  Errors ({len(report_a.errors)}):")
        for e in report_a.errors:
            print(f"    [FAIL] {e}")
    if report_a.warnings:
        print(f"\n  Warnings ({len(report_a.warnings)}):")
        for w in report_a.warnings:
            print(f"    [WARN] {w}")

    # ── 4. Export to CSV / JSON / SQL ───────────────────────────────────────
    print_section("EXPORT: CSV / JSON / SQL Seed")
    t_exp = time.time()
    exporter = DataExporter(cfg.exports_dir)
    exported = exporter.export_all(dataset_a, anomalies_a)
    exp_time = time.time() - t_exp
    print(f"  Export directory : {cfg.exports_dir}")
    print(f"  SQL Seed file    : {exported['sql']}")
    csv_count  = len([k for k in exported if k.startswith("csv_")])
    json_count = len([k for k in exported if k.startswith("json_")])
    print(f"  CSV files        : {csv_count}")
    print(f"  JSON files       : {json_count}")
    print(f"  Ground truth     : {exported.get('gt_csv')}")
    print(f"  Exported in {exp_time:.2f}s")

    # ── 5. SHA-256 checksums (Run 1) ────────────────────────────────────────
    print_section("SHA-256 CHECKSUMS (Run 1)")
    checksums_a = compute_checksums(dataset_a)
    for table, chk in checksums_a.items():
        print(f"  {table:40s}: {chk}")

    # ── 6. Second generation run (reproducibility) ──────────────────────────
    print_section("RUN 2: Reproducibility Check (same seed)")
    t1 = time.time()
    dataset_b, anomalies_b, report_b = generate_dataset(cfg)
    gen2_time = time.time() - t1
    print(f"  Completed in {gen2_time:.2f}s")

    checksums_b = compute_checksums(dataset_b)

    # ── 7. Reproducibility report ───────────────────────────────────────────
    print_section("REPRODUCIBILITY VERIFICATION")
    all_match = True
    for table in checksums_a:
        a_chk = checksums_a[table]
        b_chk = checksums_b.get(table, "MISSING")
        match = a_chk == b_chk
        if not match:
            all_match = False
        icon = "✓" if match else "✗"
        print(f"  {icon}  {table:40s}  {a_chk[:20]}...")

    # Row counts match check
    count_match = all(
        len(dataset_a[t]) == len(dataset_b.get(t, []))
        for t in dataset_a
    )
    anomaly_count_match = len(anomalies_a) == len(anomalies_b)

    print(f"\n  Row counts match : {'YES' if count_match else 'NO'}")
    print(f"  Anomaly count    : Run1={len(anomalies_a)}, Run2={len(anomalies_b)}  {'✓' if anomaly_count_match else '✗'}")
    print(f"\n  Overall result   : {'ALL CHECKSUMS IDENTICAL ✓' if all_match else 'MISMATCHES FOUND ✗'}")

    # ── 8. Final summary ────────────────────────────────────────────────────
    print_section("FINAL SUMMARY")
    print(f"  Profile         : {cfg.profile_name}")
    print(f"  Seed            : {cfg.seed}")
    print(f"  Generation time : Run1={gen1_time:.2f}s  Run2={gen2_time:.2f}s")
    print(f"  Validation      : {'PASSED' if report_a.is_valid else 'FAILED'}")
    print(f"  Reproducibility : {'CONFIRMED' if all_match else 'FAILED'}")
    print()

    # Report actual volumes vs targets
    actual_courses    = len(dataset_a["courses"])
    actual_learners   = len(dataset_a["learners"])
    actual_enrollments = len(dataset_a["enrollments"])
    actual_assignments = len(dataset_a["assignments"])
    actual_rubrics    = len(dataset_a["rubrics"])
    actual_criteria   = len(dataset_a["rubric_criteria"])
    actual_submissions = len(dataset_a["submissions"])
    actual_grades     = len(dataset_a["grades"])
    actual_gcs        = len(dataset_a["grade_criterion_scores"])
    actual_feedback   = len(dataset_a["feedbacks"])
    actual_resubs     = len(dataset_a["resubmissions"])
    actual_appeals    = len(dataset_a["appeals"])
    actual_audit      = len(dataset_a["audit_logs"])
    actual_artifacts  = len(dataset_a["submission_artifacts"])
    actual_ssh        = len(dataset_a["submission_status_histories"])

    print(f"  {'Entity':<40} {'Target':>10}  {'Actual':>10}  {'Met?':>6}")
    print(f"  {'-'*70}")
    checks = [
        ("Courses",                  cfg.num_courses,       actual_courses,        cfg.num_courses),
        ("Learners",                 cfg.num_learners,      actual_learners,       cfg.num_learners),
        ("Enrollments",              "≥20,000",             actual_enrollments,    20000),
        ("Assignments",              cfg.num_assignments,   actual_assignments,    cfg.num_assignments),
        ("Rubrics",                  "≥1,000",              actual_rubrics,        1000),
        ("Rubric Criteria",          "≥5,000",              actual_criteria,       5000),
        ("Submissions (attempt 1)",  cfg.num_submissions,   actual_submissions,    cfg.num_submissions),
        ("Grades",                   "≥27,000",             actual_grades,         27000),
        ("Grade Criterion Scores",   "≥135,000",            actual_gcs,            135000),
        ("Feedbacks",                "≥27,000",             actual_feedback,       27000),
        ("Resubmissions",            "≥2,700",              actual_resubs,         2700),
        ("Appeals",                  "≥1,350",              actual_appeals,        1350),
        ("Audit Logs",               "≥1",                  actual_audit,          1),
        ("Submission Artifacts",     "≥30,000",             actual_artifacts,      30000),
        ("Status Histories",         "≥30,000",             actual_ssh,            30000),
    ]
    all_targets_met = True
    for name, target, actual, min_val in checks:
        met = actual >= min_val if isinstance(min_val, int) else True
        if not met:
            all_targets_met = False
        icon = "✓" if met else "✗"
        print(f"  {icon}  {name:<40} {str(target):>10}  {actual:>10,}  {'YES' if met else 'NO':>6}")

    print(f"\n  All targets met  : {'YES ✓' if all_targets_met else 'NO ✗'}")
    print(f"  Anomaly scenarios: {[a['scenario_id'] for a in anomalies_a]}")

    # ── Return exit code based on success ───────────────────────────────────
    success = report_a.is_valid and all_match and all_targets_met
    if not success:
        print("\n[ERROR] Generation pipeline encountered issues. See above for details.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Full dataset generation, validation, export, and reproducibility check complete.")
        sys.exit(0)


if __name__ == "__main__":
    main()
