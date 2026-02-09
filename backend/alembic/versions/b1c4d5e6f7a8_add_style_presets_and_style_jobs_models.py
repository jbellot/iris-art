"""add_style_presets_and_style_jobs_models

Revision ID: b1c4d5e6f7a8
Revises: af6e288f1a0a
Create Date: 2026-02-09 17:47:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c4d5e6f7a8'
down_revision: Union[str, None] = 'af6e288f1a0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create style_presets table
    op.create_table(
        'style_presets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('ABSTRACT', 'WATERCOLOR', 'OIL_PAINTING', 'GEOMETRIC', 'COSMIC', 'NATURE', 'POP_ART', 'MINIMALIST', name='stylecategory'), nullable=False),
        sa.Column('tier', sa.Enum('FREE', 'PREMIUM', name='styletier'), nullable=False),
        sa.Column('thumbnail_s3_key', sa.String(length=255), nullable=True),
        sa.Column('model_s3_key', sa.String(length=255), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_style_presets_name'), 'style_presets', ['name'], unique=True)
    op.create_index(op.f('ix_style_presets_tier'), 'style_presets', ['tier'], unique=False)

    # Create style_jobs table
    op.create_table(
        'style_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('photo_id', sa.UUID(), nullable=False),
        sa.Column('processing_job_id', sa.UUID(), nullable=True),
        sa.Column('style_preset_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='stylejobstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('preview_s3_key', sa.String(length=255), nullable=True),
        sa.Column('result_s3_key', sa.String(length=255), nullable=True),
        sa.Column('result_width', sa.Integer(), nullable=True),
        sa.Column('result_height', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_type', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ),
        sa.ForeignKeyConstraint(['processing_job_id'], ['processing_jobs.id'], ),
        sa.ForeignKeyConstraint(['style_preset_id'], ['style_presets.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_style_jobs_photo_id'), 'style_jobs', ['photo_id'], unique=False)
    op.create_index(op.f('ix_style_jobs_processing_job_id'), 'style_jobs', ['processing_job_id'], unique=False)
    op.create_index(op.f('ix_style_jobs_style_preset_id'), 'style_jobs', ['style_preset_id'], unique=False)
    op.create_index(op.f('ix_style_jobs_user_id'), 'style_jobs', ['user_id'], unique=False)

    # Seed style presets
    style_presets_table = sa.table(
        'style_presets',
        sa.column('id', sa.UUID()),
        sa.column('name', sa.String()),
        sa.column('display_name', sa.String()),
        sa.column('description', sa.Text()),
        sa.column('category', sa.String()),
        sa.column('tier', sa.String()),
        sa.column('thumbnail_s3_key', sa.String()),
        sa.column('model_s3_key', sa.String()),
        sa.column('sort_order', sa.Integer()),
        sa.column('is_active', sa.Boolean()),
    )

    # Free styles (5)
    free_styles = [
        {
            'id': str(uuid4()),
            'name': 'cosmic_iris',
            'display_name': 'Cosmic Iris',
            'description': 'Transform your iris into a cosmic nebula with swirling galaxies and starlight',
            'category': 'COSMIC',
            'tier': 'FREE',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/cosmic_iris.onnx',
            'sort_order': 0,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'watercolor_dream',
            'display_name': 'Watercolor Dream',
            'description': 'Soft, flowing watercolor painting with gentle brush strokes',
            'category': 'WATERCOLOR',
            'tier': 'FREE',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/watercolor_dream.onnx',
            'sort_order': 1,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'pop_vision',
            'display_name': 'Pop Vision',
            'description': 'Bold pop art style with vibrant colors and strong contrasts',
            'category': 'POP_ART',
            'tier': 'FREE',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/pop_vision.onnx',
            'sort_order': 2,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'minimal_lines',
            'display_name': 'Minimal Lines',
            'description': 'Clean, minimalist design with elegant line work',
            'category': 'MINIMALIST',
            'tier': 'FREE',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/minimal_lines.onnx',
            'sort_order': 3,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'natures_eye',
            'display_name': "Nature's Eye",
            'description': 'Organic patterns inspired by leaves, flowers, and natural textures',
            'category': 'NATURE',
            'tier': 'FREE',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/natures_eye.onnx',
            'sort_order': 4,
            'is_active': True,
        },
    ]

    # Premium styles (10)
    premium_styles = [
        {
            'id': str(uuid4()),
            'name': 'oil_master',
            'display_name': 'Oil Master',
            'description': 'Rich, textured oil painting with classical techniques',
            'category': 'OIL_PAINTING',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/oil_master.onnx',
            'sort_order': 0,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'neon_pulse',
            'display_name': 'Neon Pulse',
            'description': 'Electric neon glow with futuristic abstract patterns',
            'category': 'ABSTRACT',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/neon_pulse.onnx',
            'sort_order': 1,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'crystal_geometry',
            'display_name': 'Crystal Geometry',
            'description': 'Crystalline geometric patterns with sharp, prismatic edges',
            'category': 'GEOMETRIC',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/crystal_geometry.onnx',
            'sort_order': 2,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'aurora_flow',
            'display_name': 'Aurora Flow',
            'description': 'Flowing northern lights with ethereal color gradients',
            'category': 'COSMIC',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/aurora_flow.onnx',
            'sort_order': 3,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'monets_garden',
            'display_name': "Monet's Garden",
            'description': 'Impressionist masterpiece inspired by Claude Monet',
            'category': 'WATERCOLOR',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/monets_garden.onnx',
            'sort_order': 4,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'stained_glass',
            'display_name': 'Stained Glass',
            'description': 'Luminous stained glass window with colored light',
            'category': 'GEOMETRIC',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/stained_glass.onnx',
            'sort_order': 5,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'digital_glitch',
            'display_name': 'Digital Glitch',
            'description': 'Cyberpunk glitch art with digital artifacts and distortion',
            'category': 'ABSTRACT',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/digital_glitch.onnx',
            'sort_order': 6,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'golden_hour',
            'display_name': 'Golden Hour',
            'description': 'Warm, golden sunset glow with natural amber tones',
            'category': 'NATURE',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/golden_hour.onnx',
            'sort_order': 7,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'ink_wash',
            'display_name': 'Ink Wash',
            'description': 'Traditional East Asian ink wash painting (sumi-e)',
            'category': 'MINIMALIST',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/ink_wash.onnx',
            'sort_order': 8,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'fire_and_ice',
            'display_name': 'Fire & Ice',
            'description': 'Dramatic contrast of fiery reds and icy blues',
            'category': 'ABSTRACT',
            'tier': 'PREMIUM',
            'thumbnail_s3_key': None,
            'model_s3_key': 'styles/fire_and_ice.onnx',
            'sort_order': 9,
            'is_active': True,
        },
    ]

    # Insert all style presets
    op.bulk_insert(style_presets_table, free_styles + premium_styles)


def downgrade() -> None:
    op.drop_index(op.f('ix_style_jobs_user_id'), table_name='style_jobs')
    op.drop_index(op.f('ix_style_jobs_style_preset_id'), table_name='style_jobs')
    op.drop_index(op.f('ix_style_jobs_processing_job_id'), table_name='style_jobs')
    op.drop_index(op.f('ix_style_jobs_photo_id'), table_name='style_jobs')
    op.drop_table('style_jobs')
    op.drop_index(op.f('ix_style_presets_tier'), table_name='style_presets')
    op.drop_index(op.f('ix_style_presets_name'), table_name='style_presets')
    op.drop_table('style_presets')

    # Drop custom enums
    op.execute('DROP TYPE stylejobstatus')
    op.execute('DROP TYPE styletier')
    op.execute('DROP TYPE stylecategory')
