"""remove_goal_type_and_status_from_sales_plans

Revision ID: b5cf498bcad7
Revises: 4bf38268cf4c
Create Date: 2025-10-17 20:53:24.726138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5cf498bcad7'
down_revision: Union[str, Sequence[str], None] = '4bf38268cf4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Remove goal_type and status columns."""
    # Drop goal_type column
    op.drop_column('sales_plans', 'goal_type')

    # Drop status column
    op.drop_column('sales_plans', 'status')


def downgrade() -> None:
    """Downgrade schema: Re-add goal_type and status columns."""
    # Re-add status column
    op.add_column('sales_plans',
        sa.Column('status', sa.Enum('active', 'completed', 'deactive', name='status'), nullable=False, server_default='active')
    )

    # Re-add goal_type column
    op.add_column('sales_plans',
        sa.Column('goal_type', sa.Enum('sales', 'orders', name='goaltype'), nullable=False, server_default='sales')
    )
