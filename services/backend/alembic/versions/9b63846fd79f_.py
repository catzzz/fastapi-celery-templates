"""empty message

Revision ID: 9b63846fd79f
Revises: 27fefc78bdbe
Create Date: 2024-09-16 07:17:01.685949

"""

from typing import (
    Sequence,
    Union,
)

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b63846fd79f"
down_revision: Union[str, None] = "27fefc78bdbe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("users")
    # ### end Alembic commands ###
