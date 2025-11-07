"""Fix metodo_creacion to string type

Revision ID: c6d7e8f9g0h1
Revises: a5d4684abb15
Create Date: 2025-11-07 00:00:00.000000

Changes metodo_creacion from ENUM to VARCHAR(50) to match model definition.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6d7e8f9g0h1'
down_revision: Union[str, None] = 'a5d4684abb15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert metodo_creacion from ENUM to VARCHAR(50).

    This fixes the type mismatch between database (ENUM) and model (String).
    """
    # Convert existing ENUM values to strings
    op.execute("""
        ALTER TABLE orders
        ALTER COLUMN metodo_creacion TYPE VARCHAR(50)
        USING metodo_creacion::text
    """)

    # Drop the ENUM type (if no other table uses it)
    op.execute("DROP TYPE IF EXISTS creationmethod")


def downgrade() -> None:
    """Revert back to ENUM type."""
    # Recreate ENUM type
    op.execute("""
        CREATE TYPE creationmethod AS ENUM (
            'visita_vendedor',
            'app_cliente',
            'app_vendedor'
        )
    """)

    # Convert VARCHAR back to ENUM
    op.execute("""
        ALTER TABLE orders
        ALTER COLUMN metodo_creacion TYPE creationmethod
        USING metodo_creacion::creationmethod
    """)
