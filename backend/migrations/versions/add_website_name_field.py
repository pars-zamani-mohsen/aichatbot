"""add website name field

Revision ID: add_website_name_field
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_website_name_field'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # اضافه کردن فیلد name به جدول websites
    op.add_column('websites', sa.Column('name', sa.String(), nullable=True))


def downgrade() -> None:
    # حذف فیلد name از جدول websites
    op.drop_column('websites', 'name') 