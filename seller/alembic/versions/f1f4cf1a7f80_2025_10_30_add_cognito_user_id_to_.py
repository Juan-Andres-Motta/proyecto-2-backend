"""2025_10_30_add_cognito_user_id_to_sellers

Revision ID: f1f4cf1a7f80
Revises: b5cf498bcad7
Create Date: 2025-10-30 12:14:43.325080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1f4cf1a7f80'
down_revision: Union[str, Sequence[str], None] = 'b5cf498bcad7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add column as nullable
    op.add_column('sellers', sa.Column('cognito_user_id', sa.String(length=255), nullable=True))

    # Step 2: Set temporary value for existing sellers (will be updated manually or through admin)
    # Using a placeholder that clearly indicates it needs to be updated
    op.execute("UPDATE sellers SET cognito_user_id = 'PENDING_' || id::text WHERE cognito_user_id IS NULL")

    # Step 3: Make column NOT NULL and add unique constraint
    op.alter_column('sellers', 'cognito_user_id', nullable=False)
    op.create_unique_constraint('sellers_cognito_user_id_key', 'sellers', ['cognito_user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('sellers_cognito_user_id_key', 'sellers', type_='unique')
    op.drop_column('sellers', 'cognito_user_id')
