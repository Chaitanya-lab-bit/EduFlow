"""initial_eduflow_schema

Revision ID: 0001_initial_eduflow_schema
Revises: 
Create Date: 2026-10-30 11:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_eduflow_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Course table
    op.create_table(
        'course',
        sa.Column('course_id', sa.String(length=32), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('term', sa.String(length=32), nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='draft', nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('end_date > start_date', name='chk_course_dates'),
        sa.PrimaryKeyConstraint('course_id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_course_code', 'course', ['code'])
    op.create_index('idx_course_status', 'course', ['status'])

    # 2. Learner table
    op.create_table(
        'learner',
        sa.Column('learner_id', sa.String(length=32), nullable=False),
        sa.Column('student_number', sa.String(length=64), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('learner_id'),
        sa.UniqueConstraint('student_number'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_learner_email', 'learner', ['email'])
    op.create_index('idx_learner_student_number', 'learner', ['student_number'])

    # 3. Enrollment table
    op.create_table(
        'enrollment',
        sa.Column('enrollment_id', sa.String(length=32), nullable=False),
        sa.Column('course_id', sa.String(length=32), nullable=False),
        sa.Column('learner_id', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('dropped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.course_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['learner_id'], ['learner.learner_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('enrollment_id'),
        sa.UniqueConstraint('course_id', 'learner_id', name='uq_course_learner')
    )
    op.create_index('idx_enrollment_course', 'enrollment', ['course_id'])
    op.create_index('idx_enrollment_learner', 'enrollment', ['learner_id'])
    op.create_index('idx_enrollment_status', 'enrollment', ['status'])

    # 4. Assignment table
    op.create_table(
        'assignment',
        sa.Column('assignment_id', sa.String(length=32), nullable=False),
        sa.Column('course_id', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_score', sa.Numeric(precision=5, scale=2), server_default='100.00', nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cutoff_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('late_penalty_per_day', sa.Numeric(precision=4, scale=2), server_default='5.00', nullable=False),
        sa.Column('max_late_days', sa.Integer(), server_default='3', nullable=False),
        sa.Column('grace_period_minutes', sa.Integer(), server_default='15', nullable=False),
        sa.Column('max_resubmissions', sa.Integer(), server_default='1', nullable=False),
        sa.Column('required_artifact_types', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('max_score > 0', name='chk_assignment_max_score'),
        sa.CheckConstraint('cutoff_date >= due_date', name='chk_assignment_dates'),
        sa.CheckConstraint('late_penalty_per_day >= 0 AND late_penalty_per_day <= 100', name='chk_assignment_penalty'),
        sa.CheckConstraint('grace_period_minutes >= 0', name='chk_assignment_grace'),
        sa.CheckConstraint('max_resubmissions >= 0', name='chk_assignment_resubmissions'),
        sa.ForeignKeyConstraint(['course_id'], ['course.course_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('assignment_id')
    )
    op.create_index('idx_assignment_course', 'assignment', ['course_id'])
    op.create_index('idx_assignment_status', 'assignment', ['status'])
    op.create_index('idx_assignment_due_date', 'assignment', ['due_date'])

    # 5. Rubric table
    op.create_table(
        'rubric',
        sa.Column('rubric_id', sa.String(length=64), nullable=False),
        sa.Column('assignment_id', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_points', sa.Numeric(precision=5, scale=2), server_default='100.00', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('total_points > 0', name='chk_rubric_total_points'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.assignment_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('rubric_id'),
        sa.UniqueConstraint('assignment_id', 'version', name='uq_rubric_assignment_version')
    )
    op.create_index('idx_rubric_assignment', 'rubric', ['assignment_id'])

    # 6. RubricCriterion table
    op.create_table(
        'rubric_criterion',
        sa.Column('criterion_id', sa.String(length=96), nullable=False),
        sa.Column('rubric_id', sa.String(length=64), nullable=False),
        sa.Column('criterion_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_points', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('weight', sa.Numeric(precision=4, scale=2), server_default='1.00', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('max_points > 0', name='chk_criterion_max_points'),
        sa.CheckConstraint('weight > 0', name='chk_criterion_weight'),
        sa.ForeignKeyConstraint(['rubric_id'], ['rubric.rubric_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('criterion_id')
    )
    op.create_index('idx_criterion_rubric', 'rubric_criterion', ['rubric_id'])

    # 7. Submission table
    op.create_table(
        'submission',
        sa.Column('submission_id', sa.String(length=96), nullable=False),
        sa.Column('assignment_id', sa.String(length=32), nullable=False),
        sa.Column('learner_id', sa.String(length=32), nullable=False),
        sa.Column('enrollment_id', sa.String(length=32), nullable=False),
        sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='submitted', nullable=False),
        sa.Column('is_late', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('late_duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('late_penalty_percentage', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('raw_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('final_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('learner_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('attempt_number >= 1', name='chk_submission_attempt'),
        sa.CheckConstraint('late_duration_seconds >= 0', name='chk_submission_late_duration'),
        sa.CheckConstraint('late_penalty_percentage >= 0 AND late_penalty_percentage <= 100', name='chk_submission_late_penalty'),
        sa.CheckConstraint('(raw_score IS NULL OR raw_score >= 0) AND (final_score IS NULL OR final_score >= 0)', name='chk_submission_scores'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.assignment_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['learner_id'], ['learner.learner_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollment.enrollment_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('submission_id'),
        sa.UniqueConstraint('assignment_id', 'learner_id', 'attempt_number', name='uq_submission_attempt')
    )
    op.create_index('idx_submission_assignment', 'submission', ['assignment_id'])
    op.create_index('idx_submission_learner', 'submission', ['learner_id'])
    op.create_index('idx_submission_status', 'submission', ['status'])
    op.create_index('idx_submission_submitted_at', 'submission', ['submitted_at'])
    op.create_index('idx_submission_lookup', 'submission', ['assignment_id', 'learner_id', 'status'])

    # 8. SubmissionArtifact table
    op.create_table(
        'submission_artifact',
        sa.Column('artifact_id', sa.String(length=128), nullable=False),
        sa.Column('submission_id', sa.String(length=96), nullable=False),
        sa.Column('artifact_type', sa.String(length=64), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=128), nullable=False),
        sa.Column('storage_uri', sa.String(length=512), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('file_size_bytes > 0', name='chk_artifact_size'),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.submission_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('artifact_id'),
        sa.UniqueConstraint('submission_id', 'artifact_type', name='uq_submission_artifact_type')
    )
    op.create_index('idx_artifact_submission', 'submission_artifact', ['submission_id'])
    op.create_index('idx_artifact_type', 'submission_artifact', ['artifact_type'])

    # 9. Grade table
    op.create_table(
        'grade',
        sa.Column('grade_id', sa.String(length=112), nullable=False),
        sa.Column('submission_id', sa.String(length=96), nullable=False),
        sa.Column('graded_by', sa.String(length=64), nullable=False),
        sa.Column('raw_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('late_penalty_applied', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('bonus_points', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('final_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('is_final', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('grade_status', sa.String(length=32), server_default='provisional', nullable=False),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('raw_score >= 0 AND late_penalty_applied >= 0 AND bonus_points >= 0 AND final_score >= 0', name='chk_grade_scores'),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.submission_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('grade_id'),
        sa.UniqueConstraint('submission_id')
    )
    op.create_index('idx_grade_submission', 'grade', ['submission_id'])
    op.create_index('idx_grade_status', 'grade', ['grade_status'])
    op.create_index('idx_grade_graded_by', 'grade', ['graded_by'])

    # 10. GradeCriterionScore table
    op.create_table(
        'grade_criterion_score',
        sa.Column('score_id', sa.String(length=128), nullable=False),
        sa.Column('grade_id', sa.String(length=112), nullable=False),
        sa.Column('criterion_id', sa.String(length=96), nullable=False),
        sa.Column('score_awarded', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('evaluator_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('score_awarded >= 0', name='chk_criterion_score_awarded'),
        sa.ForeignKeyConstraint(['grade_id'], ['grade.grade_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criterion_id'], ['rubric_criterion.criterion_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('score_id'),
        sa.UniqueConstraint('grade_id', 'criterion_id', name='uq_grade_criterion')
    )
    op.create_index('idx_gcs_grade', 'grade_criterion_score', ['grade_id'])
    op.create_index('idx_gcs_criterion', 'grade_criterion_score', ['criterion_id'])

    # 11. Feedback table
    op.create_table(
        'feedback',
        sa.Column('feedback_id', sa.String(length=128), nullable=False),
        sa.Column('grade_id', sa.String(length=112), nullable=False),
        sa.Column('submission_id', sa.String(length=96), nullable=False),
        sa.Column('author_id', sa.String(length=64), nullable=False),
        sa.Column('visibility', sa.String(length=32), server_default='learner_visible', nullable=False),
        sa.Column('general_comments', sa.Text(), nullable=False),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('areas_for_improvement', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['grade_id'], ['grade.grade_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.submission_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('feedback_id')
    )
    op.create_index('idx_feedback_grade', 'feedback', ['grade_id'])
    op.create_index('idx_feedback_submission', 'feedback', ['submission_id'])

    # 12. Resubmission table
    op.create_table(
        'resubmission',
        sa.Column('resubmission_id', sa.String(length=32), nullable=False),
        sa.Column('original_submission_id', sa.String(length=96), nullable=False),
        sa.Column('new_submission_id', sa.String(length=96), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='submitted', nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('original_submission_id <> new_submission_id', name='chk_resubmission_distinct'),
        sa.ForeignKeyConstraint(['original_submission_id'], ['submission.submission_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['new_submission_id'], ['submission.submission_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('resubmission_id'),
        sa.UniqueConstraint('new_submission_id')
    )
    op.create_index('idx_resubmission_original', 'resubmission', ['original_submission_id'])
    op.create_index('idx_resubmission_new', 'resubmission', ['new_submission_id'])

    # 13. Appeal table
    op.create_table(
        'appeal',
        sa.Column('appeal_id', sa.String(length=32), nullable=False),
        sa.Column('submission_id', sa.String(length=96), nullable=False),
        sa.Column('grade_id', sa.String(length=112), nullable=False),
        sa.Column('learner_id', sa.String(length=32), nullable=False),
        sa.Column('reviewed_by', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='submitted', nullable=False),
        sa.Column('reason_category', sa.String(length=64), nullable=False),
        sa.Column('learner_statement', sa.Text(), nullable=False),
        sa.Column('contested_criteria', sa.JSON(), nullable=True),
        sa.Column('original_grade', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('requested_grade', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('final_grade', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('decision_notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('original_grade >= 0 AND (requested_grade IS NULL OR requested_grade >= 0) AND (final_grade IS NULL OR final_grade >= 0)', name='chk_appeal_grades'),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.submission_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['grade_id'], ['grade.grade_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['learner_id'], ['learner.learner_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('appeal_id')
    )
    op.create_index('idx_appeal_submission', 'appeal', ['submission_id'])
    op.create_index('idx_appeal_grade', 'appeal', ['grade_id'])
    op.create_index('idx_appeal_learner', 'appeal', ['learner_id'])
    op.create_index('idx_appeal_status', 'appeal', ['status'])
    op.create_index('idx_appeal_submitted_at', 'appeal', ['submitted_at'])

    # 14. SubmissionStatusHistory table
    op.create_table(
        'submission_status_history',
        sa.Column('history_id', sa.String(length=32), nullable=False),
        sa.Column('submission_id', sa.String(length=96), nullable=False),
        sa.Column('old_status', sa.String(length=32), nullable=True),
        sa.Column('new_status', sa.String(length=32), nullable=False),
        sa.Column('changed_by', sa.String(length=64), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.submission_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('history_id')
    )
    op.create_index('idx_ssh_submission', 'submission_status_history', ['submission_id'])
    op.create_index('idx_ssh_changed_at', 'submission_status_history', ['changed_at'])

    # 15. AuditLog table
    op.create_table(
        'audit_log',
        sa.Column('audit_id', sa.String(length=32), nullable=False),
        sa.Column('entity_name', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=128), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('actor_role', sa.String(length=32), server_default='system', nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('audit_id')
    )
    op.create_index('idx_audit_entity', 'audit_log', ['entity_name', 'entity_id'])
    op.create_index('idx_audit_timestamp', 'audit_log', ['timestamp'])
    op.create_index('idx_audit_actor', 'audit_log', ['actor_id'])
    op.create_index('idx_audit_action', 'audit_log', ['action'])


def downgrade():
    op.drop_table('audit_log')
    op.drop_table('submission_status_history')
    op.drop_table('appeal')
    op.drop_table('resubmission')
    op.drop_table('feedback')
    op.drop_table('grade_criterion_score')
    op.drop_table('grade')
    op.drop_table('submission_artifact')
    op.drop_table('submission')
    op.drop_table('rubric_criterion')
    op.drop_table('rubric')
    op.drop_table('assignment')
    op.drop_table('enrollment')
    op.drop_table('learner')
    op.drop_table('course')
