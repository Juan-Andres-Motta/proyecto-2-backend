"""2025_10_13_rename stores to warehouses

Revision ID: d8f5c9a1e234
Revises: 6b6951d1f673
Create Date: 2025-10-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f5c9a1e234'
down_revision: Union[str, Sequence[str], None] = '6b6951d1f673'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename stores table to warehouses
    op.rename_table('stores', 'warehouses')

    # Rename store_id column to warehouse_id in inventories table
    op.alter_column('inventories', 'store_id', new_column_name='warehouse_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename warehouses table back to stores
    op.rename_table('warehouses', 'stores')

    # Rename warehouse_id column back to store_id in inventories table
    op.alter_column('inventories', 'warehouse_id', new_column_name='store_id')
