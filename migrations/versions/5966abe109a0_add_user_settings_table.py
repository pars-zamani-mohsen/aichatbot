"""add user settings table

Revision ID: 5966abe109a0
Revises: 1a222b870456
Create Date: 2025-08-30 11:33:25.736187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5966abe109a0'
down_revision: Union[str, None] = '1a222b870456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 