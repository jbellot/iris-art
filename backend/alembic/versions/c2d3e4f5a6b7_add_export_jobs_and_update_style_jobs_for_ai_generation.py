"""add export jobs and update style jobs for ai generation

Revision ID: c2d3e4f5a6b7
Revises: b1c4d5e6f7a8
Create Date: 2026-02-09 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update style_jobs.style_preset_id to be nullable (for AI generation)
    op.alter_column('style_jobs', 'style_preset_id',
               existing_type=postgresql.UUID(),
               nullable=True)

    # Create export_jobs table
    op.create_table('export_jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('source_type', sa.Enum('STYLED', 'AI_GENERATED', 'PROCESSED', name='exportsourcetype'), nullable=False),
    sa.Column('source_job_id', sa.String(length=36), nullable=False),
    sa.Column('source_s3_key', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='exportjobstatus'), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=False),
    sa.Column('current_step', sa.String(length=100), nullable=True),
    sa.Column('celery_task_id', sa.String(length=255), nullable=True),
    sa.Column('is_paid', sa.Boolean(), nullable=False),
    sa.Column('result_s3_key', sa.String(length=255), nullable=True),
    sa.Column('result_width', sa.Integer(), nullable=True),
    sa.Column('result_height', sa.Integer(), nullable=True),
    sa.Column('file_size_bytes', sa.Integer(), nullable=True),
    sa.Column('processing_time_ms', sa.Integer(), nullable=True),
    sa.Column('error_type', sa.String(length=50), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_export_jobs_source_job_id'), 'export_jobs', ['source_job_id'], unique=False)
    op.create_index(op.f('ix_export_jobs_user_id'), 'export_jobs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_export_jobs_user_id'), table_name='export_jobs')
    op.drop_index(op.f('ix_export_jobs_source_job_id'), table_name='export_jobs')
    op.drop_table('export_jobs')

    # Revert style_jobs.style_preset_id to non-nullable
    op.alter_column('style_jobs', 'style_preset_id',
               existing_type=postgresql.UUID(),
               nullable=False)

    # Drop enums
    op.execute('DROP TYPE exportjobstatus')
    op.execute('DROP TYPE exportsourcetype')
