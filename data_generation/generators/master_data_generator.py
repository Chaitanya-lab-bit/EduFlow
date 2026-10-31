from datetime import datetime, timezone, timedelta
from faker import Faker
import numpy as np
from backend.models.enums import CourseStatus, EnrollmentStatus

DEPARTMENTS = [
    "Computer Science",
    "Data Science",
    "Software Engineering",
    "Artificial Intelligence",
    "Cybersecurity",
    "Information Systems",
    "Cloud Computing",
    "Computer Systems & Networks"
]

COURSE_TIMEZONES = [
    "America/New_York",
    "UTC",
    "America/Chicago",
    "America/Los_Angeles",
    "Europe/London",
    "Asia/Kolkata",
]

LEARNER_TIMEZONES = [
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "Europe/London",
    "Asia/Kolkata",
    "Asia/Tokyo",
    "UTC",
    "Australia/Sydney"
]

def generate_courses(num_courses: int, seed: int) -> list[dict]:
    """Generate deterministic course master records."""
    rng = np.random.default_rng(seed)
    courses = []
    
    base_start = datetime(2026, 8, 25, 0, 0, 0, tzinfo=timezone.utc)
    base_end = datetime(2026, 12, 20, 23, 59, 59, tzinfo=timezone.utc)
    
    for i in range(1, num_courses + 1):
        dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
        code_prefix = "".join(w[0] for w in dept.split()[:2]).upper()
        code = f"{code_prefix}-{500 + i}"
        course_id = f"CRS-2026-{i:06d}"
        
        # Slight variation in course schedule (1-14 days offset)
        offset_days = int(rng.integers(0, 15))
        start_date = base_start + timedelta(days=offset_days)
        end_date = base_end + timedelta(days=offset_days)
        
        tz_choice = COURSE_TIMEZONES[int(rng.integers(0, len(COURSE_TIMEZONES)))]
        
        courses.append({
            "course_id": course_id,
            "code": code,
            "title": f"Advanced {dept} Studies {i}",
            "description": f"Comprehensive graduate-level coursework in {dept}.",
            "department": dept,
            "term": "Fall 2026",
            "timezone": tz_choice,
            "status": CourseStatus.ACTIVE.value,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "created_at": (start_date - timedelta(days=30)).isoformat(),
            "updated_at": (start_date - timedelta(days=30)).isoformat(),
        })
        
    return courses

def generate_learners(num_learners: int, seed: int) -> tuple[list[dict], dict[str, float]]:
    """
    Generate deterministic learner master records.
    Returns:
        learners: list of learner dictionaries
        competency_map: dict mapping learner_id to latent competency theta in [50, 100]
    """
    fake = Faker()
    fake.seed_instance(seed)
    rng = np.random.default_rng(seed)
    
    learners = []
    competency_map = {}
    
    # Latent student competency: Beta(4.5, 2.0) scaled to [50.0, 100.0]
    betas = rng.beta(4.5, 2.0, size=num_learners)
    
    now_ref = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    for i in range(1, num_learners + 1):
        learner_id = f"LNR-2026-{i:06d}"
        student_number = f"STU-2026-{i:06d}"
        
        first_name = fake.first_name()
        last_name = fake.last_name()
        clean_first = "".join(c for c in first_name if c.isalnum()).lower()
        clean_last = "".join(c for c in last_name if c.isalnum()).lower()
        email = f"{clean_first}.{clean_last}.{i:05d}@university.edu"
        
        tz = LEARNER_TIMEZONES[int(rng.integers(0, len(LEARNER_TIMEZONES)))]
        
        # Scale Beta (0..1) to 50..100 competency
        comp = float(np.round(50.0 + 50.0 * betas[i - 1], 2))
        competency_map[learner_id] = comp
        
        created_at = now_ref + timedelta(minutes=int(rng.integers(0, 10000)))
        
        learners.append({
            "learner_id": learner_id,
            "student_number": student_number,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "timezone": tz,
            "status": EnrollmentStatus.ACTIVE.value,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        })
        
    return learners, competency_map
