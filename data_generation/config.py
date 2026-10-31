from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

MASTER_SEED = 20261022

@dataclass
class DatasetConfig:
    profile_name: str
    num_courses: int
    num_learners: int
    num_assignments: int
    num_submissions: int
    min_enrollments_per_learner: int
    max_enrollments_per_learner: int
    criteria_per_rubric: int = 5
    additional_rubric_versions: int = 0
    resubmission_rate: float = 0.10
    appeal_rate: float = 0.05
    grade_rate: float = 0.90
    seed: int = MASTER_SEED
    
    # Directory paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    exports_dir: Optional[Path] = None
    ground_truth_dir: Optional[Path] = None

    def __post_init__(self):
        if self.exports_dir is None:
            self.exports_dir = self.base_dir / "exports" / self.profile_name
        if self.ground_truth_dir is None:
            self.ground_truth_dir = self.base_dir / "ground_truth" / self.profile_name
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.ground_truth_dir.mkdir(parents=True, exist_ok=True)


STARTER_CONFIG = DatasetConfig(
    profile_name="starter",
    num_courses=5,
    num_learners=100,
    num_assignments=20,
    num_submissions=200,
    min_enrollments_per_learner=1,
    max_enrollments_per_learner=3,
    criteria_per_rubric=5,
    additional_rubric_versions=2,
    resubmission_rate=0.10,
    appeal_rate=0.05,
    grade_rate=0.90,
    seed=MASTER_SEED
)

FULL_CONFIG = DatasetConfig(
    profile_name="full",
    num_courses=100,
    num_learners=10000,
    num_assignments=1000,
    num_submissions=30000,
    min_enrollments_per_learner=2,
    max_enrollments_per_learner=4,
    criteria_per_rubric=5,
    additional_rubric_versions=20,
    resubmission_rate=0.10,
    appeal_rate=0.05,
    grade_rate=0.90,
    seed=MASTER_SEED
)

CONFIG_PROFILES = {
    "starter": STARTER_CONFIG,
    "full": FULL_CONFIG,
}
