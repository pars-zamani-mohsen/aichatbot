"""empty message

Revision ID: 1a222b870456
Revises: 5cfe71d2640b
Create Date: 2025-05-24 16:00:47.786191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a222b870456'
down_revision: Union[str, None] = '5cfe71d2640b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 