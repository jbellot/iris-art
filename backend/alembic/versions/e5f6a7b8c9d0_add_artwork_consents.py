"""add artwork consents

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-09 19:30:45.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create artwork_consents table
    op.create_table('artwork_consents',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('artwork_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('grantor_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('grantee_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('circle_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('purpose', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['artwork_id'], ['photos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['circle_id'], ['circles.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['grantee_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['grantor_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('artwork_id', 'grantee_user_id', 'purpose', name='uq_consent_artwork_grantee_purpose')
    )
    op.create_index(op.f('ix_artwork_consents_artwork_id'), 'artwork_consents', ['artwork_id'], unique=False)
    op.create_index(op.f('ix_artwork_consents_grantee_user_id'), 'artwork_consents', ['grantee_user_id'], unique=False)
    op.create_index(op.f('ix_artwork_consents_grantor_user_id'), 'artwork_consents', ['grantor_user_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_artwork_consents_grantor_user_id'), table_name='artwork_consents')
    op.drop_index(op.f('ix_artwork_consents_grantee_user_id'), table_name='artwork_consents')
    op.drop_index(op.f('ix_artwork_consents_artwork_id'), table_name='artwork_consents')

    # Drop table
    op.drop_table('artwork_consents')
