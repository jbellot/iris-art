"""add fusion artworks

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-02-09 19:39:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create fusion_artworks table
    op.create_table('fusion_artworks',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('circle_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('source_artwork_ids', postgresql.JSON(), nullable=False),
    sa.Column('fusion_type', sa.String(), nullable=False),
    sa.Column('blend_mode', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('result_s3_key', sa.String(), nullable=True),
    sa.Column('thumbnail_s3_key', sa.String(), nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.Column('processing_time_ms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['circle_id'], ['circles.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fusion_artworks_circle_id'), 'fusion_artworks', ['circle_id'], unique=False)
    op.create_index(op.f('ix_fusion_artworks_creator_id'), 'fusion_artworks', ['creator_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_fusion_artworks_creator_id'), table_name='fusion_artworks')
    op.drop_index(op.f('ix_fusion_artworks_circle_id'), table_name='fusion_artworks')

    # Drop table
    op.drop_table('fusion_artworks')
