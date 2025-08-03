"""uuid_migration_fresh_start

Revision ID: 20e21bf8e1d7
Revises: 20315c2aac43
Create Date: 2025-08-03 11:41:00.109487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20e21bf8e1d7'
down_revision: Union[str, Sequence[str], None] = '20315c2aac43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - drop all tables and recreate with UUIDs."""
    # Drop all existing tables to start fresh
    op.drop_table('checklist_items')
    op.drop_table('checklists')
    op.drop_table('policies')
    op.drop_table('users')
    op.drop_table('countries')
    
    # Drop enum types that might still exist
    op.execute("DROP TYPE IF EXISTS checkliststatus CASCADE")
    op.execute("DROP TYPE IF EXISTS checklistcategory CASCADE")
    op.execute("DROP TYPE IF EXISTS policytype CASCADE")
    op.execute("DROP TYPE IF EXISTS policystatus CASCADE")
    
    # Create countries table with UUID
    op.create_table('countries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('flag_emoji', sa.String(length=10), nullable=True),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('currency_code', sa.String(length=3), nullable=True),
        sa.Column('currency_name', sa.String(length=50), nullable=True),
        sa.Column('gdp_per_capita', sa.Float(), nullable=True),
        sa.Column('visa_required', sa.Boolean(), nullable=True),
        sa.Column('visa_types', sa.Text(), nullable=True),
        sa.Column('processing_time_days', sa.Integer(), nullable=True),
        sa.Column('application_fee_usd', sa.Float(), nullable=True),
        sa.Column('policies_last_updated', sa.DateTime(), nullable=True),
        sa.Column('data_source', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_countries_code'), 'countries', ['code'], unique=True)
    op.create_index(op.f('ix_countries_id'), 'countries', ['id'], unique=False)
    
    # Create users table with UUID and cognito_sub
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('cognito_sub', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('birthdate', sa.String(length=10), nullable=True),
        sa.Column('onboarding_complete', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_cognito_sub'), 'users', ['cognito_sub'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Create checklists table with UUID and country fields
    op.create_table('checklists',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('origin_country', sa.String(length=3), nullable=False),
        sa.Column('destination_country', sa.String(length=3), nullable=False),
        sa.Column('reason_for_moving', sa.String(length=200), nullable=True),
        sa.Column('status', sa.Enum('draft', 'in_progress', 'completed', 'archived', name='checkliststatus'), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklists_id'), 'checklists', ['id'], unique=False)
    
    # Create checklist_items table with UUID
    op.create_table('checklist_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('checklist_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Enum('pre_departure', 'arrival', 'setup', 'legal', 'financial', 'health', 'education', 'housing', 'transportation', 'other', name='checklistcategory'), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('estimated_duration_days', sa.Integer(), nullable=True),
        sa.Column('cost_estimate', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_items_id'), 'checklist_items', ['id'], unique=False)
    
    # Create policies table with UUID
    op.create_table('policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('country_code', sa.String(length=3), nullable=False),
        sa.Column('policy_type', sa.Enum('visa_requirement', 'document_requirement', 'health_requirement', 'financial_requirement', 'background_check', 'language_requirement', 'education_requirement', 'work_permit', 'residence_permit', 'citizenship', 'other', name='policytype'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('processing_time_days', sa.Integer(), nullable=True),
        sa.Column('application_fee_usd', sa.Integer(), nullable=True),
        sa.Column('validity_period_days', sa.Integer(), nullable=True),
        sa.Column('eligibility_criteria', sa.Text(), nullable=True),
        sa.Column('required_documents', sa.Text(), nullable=True),
        sa.Column('restrictions', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'pending', 'expired', name='policystatus'), nullable=True),
        sa.Column('effective_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_name', sa.String(length=200), nullable=True),
        sa.Column('last_verified', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['countries.code'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policies_id'), 'policies', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - recreate old tables."""
    # Drop new tables
    op.drop_table('policies')
    op.drop_table('checklist_items')
    op.drop_table('checklists')
    op.drop_table('users')
    op.drop_table('countries')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS checkliststatus CASCADE")
    op.execute("DROP TYPE IF EXISTS checklistcategory CASCADE")
    op.execute("DROP TYPE IF EXISTS policytype CASCADE")
    op.execute("DROP TYPE IF EXISTS policystatus CASCADE")
    
    # Recreate old tables (this would need to be implemented if we ever need to downgrade)
    pass
