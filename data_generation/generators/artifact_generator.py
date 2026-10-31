import hashlib
from datetime import datetime, timedelta
import numpy as np
from backend.models.enums import ArtifactType

MIME_TYPE_MAP = {
    "report_pdf": "application/pdf",
    "code_repository": "application/x-git",
    "dataset_csv": "text/csv",
    "video_presentation": "video/mp4",
    "supplementary_zip": "application/zip",
}

FILE_EXT_MAP = {
    "report_pdf": "pdf",
    "code_repository": "git",
    "dataset_csv": "csv",
    "video_presentation": "mp4",
    "supplementary_zip": "zip",
}

def generate_artifacts(
    submissions: list[dict],
    assignments: list[dict],
    seed: int
) -> list[dict]:
    """
    Generate deterministic artifacts for all submissions matching assignment requirements.
    Returns:
        artifacts: list of submission artifact dicts
    """
    rng = np.random.default_rng(seed)
    assignment_lookup = {a["assignment_id"]: a for a in assignments}
    
    artifacts = []
    
    for sub in submissions:
        sub_id = sub["submission_id"]
        aid = sub["assignment_id"]
        lid = sub["learner_id"]
        sub_time = datetime.fromisoformat(sub["submitted_at"])
        assignment = assignment_lookup[aid]
        cid = assignment["course_id"]
        
        art_idx = 1
        for a_type in assignment["required_artifact_types"]:
            art_id = f"ART-{sub_id}-{art_idx:02d}"
            ext = FILE_EXT_MAP.get(a_type, "bin")
            mime = MIME_TYPE_MAP.get(a_type, "application/octet-stream")
            fname = f"{lid}_{aid.lower()}_{a_type}.{ext}"
            fsize = int(rng.integers(102400, 10485760)) # 100KB to 10MB
            
            # Deterministic SHA-256 digest
            h = hashlib.sha256(f"{art_id}-{fname}-{fsize}-{seed}".encode()).hexdigest()
            
            artifact_record = {
                "artifact_id": art_id,
                "submission_id": sub_id,
                "artifact_type": a_type,
                "file_name": fname,
                "file_size_bytes": fsize,
                "mime_type": mime,
                "storage_uri": f"s3://eduflow-artifacts/{cid.lower()}/{aid.lower()}/{fname}",
                "checksum_sha256": h,
                "is_verified": True,
                "uploaded_at": (sub_time - timedelta(minutes=5)).isoformat(),
            }
            artifacts.append(artifact_record)
            art_idx += 1
            
    return artifacts
