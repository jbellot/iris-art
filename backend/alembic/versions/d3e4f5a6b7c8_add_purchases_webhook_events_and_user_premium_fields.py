"""add purchases, webhook_events, and user premium fields

Revision ID: d3e4f5a6b7c8
Revises: f6a7b8c9d0e1
Create Date: 2026-02-10 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create purchases table
    op.create_table('purchases',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('product_id', sa.String(length=100), nullable=False),
    sa.Column('transaction_id', sa.String(length=255), nullable=False),
    sa.Column('purchase_type', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('revenuecat_event_id', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('transaction_id')
    )
    op.create_index(op.f('ix_purchases_product_id'), 'purchases', ['product_id'], unique=False)
    op.create_index(op.f('ix_purchases_transaction_id'), 'purchases', ['transaction_id'], unique=True)
    op.create_index(op.f('ix_purchases_user_id'), 'purchases', ['user_id'], unique=False)

    # Create webhook_events table
    op.create_table('webhook_events',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('event_id', sa.String(length=255), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('app_user_id', sa.String(length=255), nullable=False),
    sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('processed_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id')
    )
    op.create_index(op.f('ix_webhook_events_app_user_id'), 'webhook_events', ['app_user_id'], unique=False)
    op.create_index(op.f('ix_webhook_events_event_id'), 'webhook_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)

    # Add premium and rate limiting fields to users table
    op.add_column('users', sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('monthly_ai_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_reset_month', sa.String(length=7), nullable=True))


def downgrade() -> None:
    # Remove user columns
    op.drop_column('users', 'last_reset_month')
    op.drop_column('users', 'monthly_ai_count')
    op.drop_column('users', 'is_premium')

    # Drop webhook_events table
    op.drop_index(op.f('ix_webhook_events_event_type'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_event_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_app_user_id'), table_name='webhook_events')
    op.drop_table('webhook_events')

    # Drop purchases table
    op.drop_index(op.f('ix_purchases_user_id'), table_name='purchases')
    op.drop_index(op.f('ix_purchases_transaction_id'), table_name='purchases')
    op.drop_index(op.f('ix_purchases_product_id'), table_name='purchases')
    op.drop_table('purchases')
