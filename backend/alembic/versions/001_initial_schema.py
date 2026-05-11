"""Initial migration: Create all tables.

Revision ID: 001_initial
Revises: 
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade: Create all tables."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create wines table
    op.create_table(
        'wines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wine_name', sa.String(length=255), nullable=False),
        sa.Column('producer', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=255), nullable=True),
        sa.Column('vintage', sa.Integer(), nullable=True),
        sa.Column('varietals', sa.JSON(), nullable=True),
        sa.Column('alcohol_content', sa.Float(), nullable=True),
        sa.Column('volume_ml', sa.Integer(), nullable=True),
        sa.Column('tasting_notes', sa.Text(), nullable=True),
        sa.Column('estimated_price', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wines_country'), 'wines', ['country'], unique=False)
    op.create_index(op.f('ix_wines_region'), 'wines', ['region'], unique=False)
    op.create_index(op.f('ix_wines_vintage'), 'wines', ['vintage'], unique=False)
    op.create_index(op.f('ix_wines_wine_name'), 'wines', ['wine_name'], unique=False)
    
    # Create wine_collections table
    op.create_table(
        'wine_collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('collection_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wine_collections_user_id'), 'wine_collections', ['user_id'], unique=False)
    
    # Create wine_collection_association (many-to-many)
    op.create_table(
        'wine_collection_association',
        sa.Column('wine_id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['wine_collections.id'], ),
        sa.ForeignKeyConstraint(['wine_id'], ['wines.id'], ),
        sa.PrimaryKeyConstraint('wine_id', 'collection_id')
    )
    
    # Create ocr_sessions table
    op.create_table(
        'ocr_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=512), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create reconstructions table
    op.create_table(
        'reconstructions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reconstruction_id', sa.String(length=100), nullable=False),
        sa.Column('object_type', sa.String(length=50), nullable=True, server_default='wine_bottle'),
        sa.Column('mesh_data', sa.JSON(), nullable=True),
        sa.Column('texture_url', sa.String(length=512), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('quality_setting', sa.String(length=50), nullable=True, server_default='medium'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('export_format', sa.String(length=50), nullable=True, server_default='gltf'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconstructions_reconstruction_id'), 'reconstructions', ['reconstruction_id'], unique=True)
    
    # Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('wine_id', sa.Integer(), nullable=True),
        sa.Column('reconstruction_id', sa.Integer(), nullable=True),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.Column('identification_confidence', sa.Float(), nullable=True),
        sa.Column('reconstruction_confidence', sa.Float(), nullable=True),
        sa.Column('overall_quality_score', sa.Float(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('compliance_issues', sa.JSON(), nullable=True),
        sa.Column('estimated_price', sa.Float(), nullable=True),
        sa.Column('tasting_profile', sa.JSON(), nullable=True),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reconstruction_id'], ['reconstructions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['wine_id'], ['wines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_analysis_id'), 'analyses', ['analysis_id'], unique=True)


def downgrade() -> None:
    """Downgrade: Drop all tables."""
    op.drop_index(op.f('ix_analyses_analysis_id'), table_name='analyses')
    op.drop_table('analyses')
    op.drop_index(op.f('ix_reconstructions_reconstruction_id'), table_name='reconstructions')
    op.drop_table('reconstructions')
    op.drop_table('ocr_sessions')
    op.drop_table('wine_collection_association')
    op.drop_index(op.f('ix_wine_collections_user_id'), table_name='wine_collections')
    op.drop_table('wine_collections')
    op.drop_index(op.f('ix_wines_wine_name'), table_name='wines')
    op.drop_index(op.f('ix_wines_vintage'), table_name='wines')
    op.drop_index(op.f('ix_wines_region'), table_name='wines')
    op.drop_index(op.f('ix_wines_country'), table_name='wines')
    op.drop_table('wines')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
