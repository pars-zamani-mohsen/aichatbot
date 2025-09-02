"""add 2fa fields to user settings

Revision ID: d0a6fc74363b
Revises: 5966abe109a0
Create Date: 2025-08-30 11:54:56.969411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0a6fc74363b'
down_revision: Union[str, None] = '5966abe109a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 