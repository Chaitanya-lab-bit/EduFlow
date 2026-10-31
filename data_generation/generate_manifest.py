import os
import hashlib
import json
import glob
import pandas as pd

export_dir = 'data_generation/exports/full'
csv_files = sorted(glob.glob(os.path.join(export_dir, 'csv', '*.csv')))
json_files = sorted(glob.glob(os.path.join(export_dir, 'json', '*.json')))

manifest = {
    "seed": 20261022,
    "target_volumes": {
        "courses": 100,
        "learners": 10000,
        "assignments": 1000,
        "rubrics": 1000,
        "rubric_criteria": 5000,
        "submissions": 30000
    },
    "exported_tables": {},
    "sql_seed": {},
    "ground_truth_anomalies": {}
}

print(f"{'Table / File':<32} | {'Rows':<8} | {'CSV Size':<10} | {'CSV SHA-256':<64}")
print("-" * 125)

for cf in csv_files:
    table_name = os.path.basename(cf).replace('.csv', '')
    df = pd.read_csv(cf)
    row_count = len(df)
    csv_size = os.path.getsize(cf)
    with open(cf, 'rb') as f:
        csv_sha = hashlib.sha256(f.read()).hexdigest()

    jf = os.path.join(export_dir, 'json', f"{table_name}.json")
    json_sha = None
    json_size = None
    if os.path.exists(jf):
        json_size = os.path.getsize(jf)
        with open(jf, 'rb') as f:
            json_sha = hashlib.sha256(f.read()).hexdigest()

    manifest["exported_tables"][table_name] = {
        "row_count": row_count,
        "csv_size_bytes": csv_size,
        "csv_sha256": csv_sha,
        "json_size_bytes": json_size,
        "json_sha256": json_sha
    }
    print(f"{table_name:<32} | {row_count:<8} | {csv_size:<10} | {csv_sha}")

sql_file = os.path.join(export_dir, 'seed.sql')
if os.path.exists(sql_file):
    sql_size = os.path.getsize(sql_file)
    with open(sql_file, 'rb') as f:
        sql_sha = hashlib.sha256(f.read()).hexdigest()
    manifest["sql_seed"] = {
        "file": "seed.sql",
        "size_bytes": sql_size,
        "sha256": sql_sha
    }
    print("-" * 125)
    print(f"{'seed.sql':<32} | {'SQL Seed':<8} | {sql_size:<10} | {sql_sha}")

anom_csv = os.path.join(export_dir, 'ground_truth', 'anomalies.csv')
if os.path.exists(anom_csv):
    df_anom = pd.read_csv(anom_csv)
    with open(anom_csv, 'rb') as f:
        anom_sha = hashlib.sha256(f.read()).hexdigest()
    manifest["ground_truth_anomalies"] = {
        "count": len(df_anom),
        "sha256": anom_sha,
        "scenarios": df_anom[['scenario_id', 'scenario_name', 'expected_error', 'http_status_expected']].to_dict(orient='records')
    }
    print(f"{'ground_truth/anomalies.csv':<32} | {len(df_anom):<8} | {os.path.getsize(anom_csv):<10} | {anom_sha}")

with open(os.path.join(export_dir, 'manifest.json'), 'w') as f:
    json.dump(manifest, f, indent=2)

print("\nSaved manifest to data_generation/exports/full/manifest.json")

