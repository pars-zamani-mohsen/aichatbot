"""add name field to websites

Revision ID: add_name_field_to_websites
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_name_field_to_websites'
down_revision = None  # حذف اشاره به مایگریشن قبلی
branch_labels = None
depends_on = None


def upgrade() -> None:
    # اضافه کردن فیلد name به جدول websites
    op.add_column('websites', sa.Column('name', sa.String(), nullable=True))


def downgrade() -> None:
    # حذف فیلد name از جدول websites
    op.drop_column('websites', 'name') 