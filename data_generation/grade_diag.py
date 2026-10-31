import sys
sys.path.insert(0, '.')
from data_generation.main import generate_dataset
from data_generation.config import STARTER_CONFIG
import pandas as pd
import numpy as np

data, anomalies, report = generate_dataset(STARTER_CONFIG)

grd = pd.DataFrame(data['grades'])
sub = pd.DataFrame(data['submissions'])[['submission_id', 'assignment_id']]
asn = pd.DataFrame(data['assignments'])[['assignment_id', 'max_score']]

g = grd.merge(sub, on='submission_id', how='left').merge(asn, on='assignment_id', how='left')
expected = np.clip(
    (g['raw_score'] - g['late_penalty_applied'] + g['bonus_points']).round(2),
    0.0, g['max_score']
)
mask = (g['final_score'] - expected).abs() > 0.01
print('Mismatched grades count:', mask.sum())
print(g[mask][['grade_id','raw_score','late_penalty_applied','bonus_points','final_score','max_score','grade_status']].to_string())
