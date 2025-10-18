"""Remove fecha_entrega_deseada and make fecha_entrega_estimada nullable

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-10-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove fecha_entrega_deseada field and make fecha_entrega_estimada nullable.

    Rationale:
    - fecha_entrega_deseada is not used (customer desired date not needed)
    - fecha_entrega_estimada will be set by Delivery Service later (not at order creation)
    """
    # Make fecha_entrega_estimada nullable
    op.alter_column('orders', 'fecha_entrega_estimada',
               existing_type=sa.DATE(),
               nullable=True)

    # Drop fecha_entrega_deseada column
    op.drop_column('orders', 'fecha_entrega_deseada')


def downgrade() -> None:
    """Revert changes - add back fecha_entrega_deseada and make fecha_entrega_estimada required."""
    # Add back fecha_entrega_deseada column
    op.add_column('orders', sa.Column('fecha_entrega_deseada', sa.DATE(), nullable=True))

    # Make fecha_entrega_estimada NOT NULL again
    # Note: This may fail if there are NULL values in production
    op.alter_column('orders', 'fecha_entrega_estimada',
               existing_type=sa.DATE(),
               nullable=False)
