"""add 2fa attempts and lock fields

Revision ID: 11d8d2631e76
Revises: d0a6fc74363b
Create Date: 2025-08-30 13:04:51.529430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11d8d2631e76'
down_revision: Union[str, None] = 'd0a6fc74363b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 