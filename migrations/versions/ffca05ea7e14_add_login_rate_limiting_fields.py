"""add login rate limiting fields

Revision ID: ffca05ea7e14
Revises: 11d8d2631e76
Create Date: 2025-08-30 13:08:16.339246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffca05ea7e14'
down_revision: Union[str, None] = '11d8d2631e76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 