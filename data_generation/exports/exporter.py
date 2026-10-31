import json
from pathlib import Path
from decimal import Decimal
import pandas as pd

TABLE_SINGULAR_MAP = {
    "courses": "course",
    "learners": "learner",
    "enrollments": "enrollment",
    "assignments": "assignment",
    "rubrics": "rubric",
    "rubric_criteria": "rubric_criterion",
    "submissions": "submission",
    "submission_artifacts": "submission_artifact",
    "submission_status_histories": "submission_status_history",
    "grades": "grade",
    "grade_criterion_scores": "grade_criterion_score",
    "feedbacks": "feedback",
    "resubmissions": "resubmission",
    "appeals": "appeal",
    "audit_logs": "audit_log",
}

TOPOLOGICAL_ORDER = [
    "courses",
    "learners",
    "enrollments",
    "assignments",
    "rubrics",
    "rubric_criteria",
    "submissions",
    "submission_artifacts",
    "submission_status_histories",
    "grades",
    "grade_criterion_scores",
    "feedbacks",
    "resubmissions",
    "appeals",
    "audit_logs",
]

def format_sql_value(val) -> str:
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float, Decimal)):
        return str(val)
    if isinstance(val, (list, dict)):
        json_str = json.dumps(val).replace("'", "''")
        return f"'{json_str}'"
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"

class DataExporter:
    """Exports generated datasets into CSV, JSON, and PostgreSQL SQL seed formats."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self, data: dict[str, list[dict]], ground_truth: list[dict] = None) -> dict[str, Path]:
        """Export dataset to CSV, JSON, and SQL formats."""
        csv_files = self.export_csv(data)
        json_files = self.export_json(data)
        sql_file = self.export_sql(data)
        
        exported = {"sql": sql_file}
        exported.update({f"csv_{k}": v for k, v in csv_files.items()})
        exported.update({f"json_{k}": v for k, v in json_files.items()})
        
        if ground_truth:
            gt_csv, gt_json = self.export_ground_truth(ground_truth)
            exported["gt_csv"] = gt_csv
            exported["gt_json"] = gt_json
            
        return exported

    def export_csv(self, data: dict[str, list[dict]]) -> dict[str, Path]:
        """Export each entity table to CSV format."""
        csv_dir = self.output_dir / "csv"
        csv_dir.mkdir(parents=True, exist_ok=True)
        results = {}
        
        for table_key, records in data.items():
            if not records:
                continue
            table_name = TABLE_SINGULAR_MAP.get(table_key, table_key)
            filepath = csv_dir / f"{table_name}.csv"
            
            # Serialize JSON columns for clean CSV format
            clean_records = []
            for r in records:
                r_clean = {}
                for k, v in r.items():
                    if isinstance(v, (list, dict)):
                        r_clean[k] = json.dumps(v)
                    else:
                        r_clean[k] = v
                clean_records.append(r_clean)
                
            df = pd.DataFrame(clean_records)
            df.to_csv(filepath, index=False, encoding="utf-8")
            results[table_name] = filepath
            
        return results

    def export_json(self, data: dict[str, list[dict]]) -> dict[str, Path]:
        """Export each entity table to JSON format."""
        json_dir = self.output_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)
        results = {}
        
        for table_key, records in data.items():
            if not records:
                continue
            table_name = TABLE_SINGULAR_MAP.get(table_key, table_key)
            filepath = json_dir / f"{table_name}.json"
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)
            results[table_name] = filepath
            
        return results

    def export_sql(self, data: dict[str, list[dict]], batch_size: int = 1000) -> Path:
        """
        Generate PostgreSQL-compatible SQL seed file inserting in topological foreign-key order.
        """
        sql_path = self.output_dir / "seed.sql"
        
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write("-- EduFlow Synthetic Seed Data Export\n")
            f.write("-- Deterministically generated for YottaFlex 72-Hour Challenge\n")
            f.write("BEGIN;\n\n")
            
            for table_key in TOPOLOGICAL_ORDER:
                records = data.get(table_key, [])
                if not records:
                    continue
                table_name = TABLE_SINGULAR_MAP.get(table_key, table_key)
                columns = list(records[0].keys())
                col_names = ", ".join(columns)
                
                f.write(f"-- Table: {table_name} ({len(records)} rows)\n")
                
                # Chunk into multi-row INSERTs for fast processing
                for i in range(0, len(records), batch_size):
                    chunk = records[i:i + batch_size]
                    rows_sql = []
                    for r in chunk:
                        vals_sql = [format_sql_value(r.get(c)) for c in columns]
                        rows_sql.append(f"  ({', '.join(vals_sql)})")
                    values_block = ",\n".join(rows_sql)
                    f.write(f"INSERT INTO {table_name} ({col_names}) VALUES\n{values_block};\n\n")
                    
            f.write("COMMIT;\n")
            
        return sql_path

    def export_ground_truth(self, ground_truth: list[dict]) -> tuple[Path, Path]:
        """Export ground truth anomaly manifest to CSV and JSON."""
        gt_dir = self.output_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = gt_dir / "anomalies.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, indent=2, default=str)
            
        csv_path = gt_dir / "anomalies.csv"
        # Flatten record_payload for CSV view
        flat_records = []
        for a in ground_truth:
            item = dict(a)
            if "record_payload" in item:
                item["record_payload"] = json.dumps(item["record_payload"])
            flat_records.append(item)
            
        df = pd.DataFrame(flat_records)
        df.to_csv(csv_path, index=False, encoding="utf-8")
        
        return csv_path, json_path
