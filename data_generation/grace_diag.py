import sys
sys.path.insert(0, '.')
from data_generation.main import generate_dataset
from data_generation.config import FULL_CONFIG
import pandas as pd
import numpy as np

data, anomalies, report = generate_dataset(FULL_CONFIG)

sub = pd.DataFrame(data['submissions'])
asn = pd.DataFrame(data['assignments'])[['assignment_id', 'due_date', 'cutoff_date', 'grace_period_minutes']]
m = sub.merge(asn, on='assignment_id', how='left')

sub_time = pd.to_datetime(m['submitted_at'], format='ISO8601', utc=True)
due_time = pd.to_datetime(m['due_date'], format='ISO8601', utc=True)
grace_delta = pd.to_timedelta(m['grace_period_minutes'], unit='m')

in_grace = (sub_time > due_time) & (sub_time <= due_time + grace_delta)
grace_mask = in_grace & (m['is_late'] == True)

print('Grace period violations:', grace_mask.sum())
if grace_mask.sum() > 0:
    sample = m[grace_mask].head(5)
    print('attempt_number distribution:')
    print(sample['attempt_number'].value_counts())
    print('Sample records:')
    print(sample[['submission_id', 'submitted_at', 'due_date', 'grace_period_minutes', 'is_late', 'late_duration_seconds', 'late_penalty_percentage', 'attempt_number']].to_string())
