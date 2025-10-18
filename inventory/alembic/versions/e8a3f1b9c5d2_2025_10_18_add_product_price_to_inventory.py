"""2025_10_18_add product_price to inventory

Revision ID: e8a3f1b9c5d2
Revises: d974948bc2ee
Create Date: 2025-10-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8a3f1b9c5d2'
down_revision: Union[str, Sequence[str], None] = 'd974948bc2ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add product_price column to inventories table."""
    op.add_column(
        'inventories',
        sa.Column('product_price', sa.Numeric(10, 2), nullable=False, server_default='0.00')
    )
    # Remove server_default after adding column (it's only needed for existing rows)
    op.alter_column('inventories', 'product_price', server_default=None)


def downgrade() -> None:
    """Remove product_price column from inventories table."""
    op.drop_column('inventories', 'product_price')
