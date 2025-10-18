"""2025_10_18_refactor to hexagonal architecture

Revision ID: a1b2c3d4e5f6
Revises: 5be7ac1004ae
Create Date: 2025-10-18 00:00:00.000000

Major changes:
- Renamed client_id to customer_id
- Made seller_id, visit_id, route_id nullable
- Removed estado/status field (deferred to future sprint)
- Removed deliver_id field
- Updated CreationMethod enum values
- Added fecha_entrega_deseada, fecha_entrega_estimada
- Added denormalized customer/seller data
- Added monto_total to orders
- Renamed order_date to fecha_pedido
- Renamed destination_address to direccion_entrega
- Added ciudad_entrega, pais_entrega
- Renamed creation_method to metodo_creacion
- Updated order_items: renamed order_id to pedido_id, product_id to producto_id
- Added precio_total, denormalized product/warehouse data, batch traceability
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5be7ac1004ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to hexagonal architecture."""

    # Drop old tables and recreate with new schema
    op.drop_table('order_items')
    op.drop_table('orders')

    # Drop old enum types
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS creationmethod")

    # Create new CreationMethod enum
    op.execute("""
        CREATE TYPE creationmethod AS ENUM (
            'visita_vendedor',
            'app_cliente',
            'app_vendedor'
        )
    """)

    # Create orders table with new schema
    op.create_table(
        'orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.UUID(), nullable=False),
        sa.Column('seller_id', sa.UUID(), nullable=True),
        sa.Column('visit_id', sa.UUID(), nullable=True),
        sa.Column('route_id', sa.UUID(), nullable=True),

        sa.Column('fecha_pedido', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_entrega_deseada', sa.Date(), nullable=True),
        sa.Column('fecha_entrega_estimada', sa.Date(), nullable=False),

        sa.Column('metodo_creacion', sa.Enum('visita_vendedor', 'app_cliente', 'app_vendedor', name='creationmethod'), nullable=False),

        sa.Column('direccion_entrega', sa.String(500), nullable=False),
        sa.Column('ciudad_entrega', sa.String(100), nullable=False),
        sa.Column('pais_entrega', sa.String(100), nullable=False),

        # Denormalized customer data
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('customer_phone', sa.String(50), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),

        # Denormalized seller data (optional)
        sa.Column('seller_name', sa.String(255), nullable=True),
        sa.Column('seller_email', sa.String(255), nullable=True),

        # Stored total
        sa.Column('monto_total', sa.Numeric(10, 2), nullable=False, server_default='0.00'),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id')
    )

    # Create order_items table with new schema
    op.create_table(
        'order_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('pedido_id', sa.UUID(), nullable=False),
        sa.Column('producto_id', sa.UUID(), nullable=False),
        sa.Column('inventario_id', sa.UUID(), nullable=False),

        # Quantities and pricing
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(10, 2), nullable=False),
        sa.Column('precio_total', sa.Numeric(10, 2), nullable=False),

        # Denormalized product data
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('product_sku', sa.String(100), nullable=False),

        # Denormalized warehouse data
        sa.Column('warehouse_id', sa.UUID(), nullable=False),
        sa.Column('warehouse_name', sa.String(255), nullable=False),
        sa.Column('warehouse_city', sa.String(100), nullable=False),
        sa.Column('warehouse_country', sa.String(100), nullable=False),

        # Batch traceability
        sa.Column('batch_number', sa.String(100), nullable=False),
        sa.Column('expiration_date', sa.Date(), nullable=False),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['pedido_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema (revert to old structure)."""

    # Drop new tables
    op.drop_table('order_items')
    op.drop_table('orders')

    # Drop new enum
    op.execute("DROP TYPE IF EXISTS creationmethod")

    # Recreate old enum types
    op.execute("""
        CREATE TYPE orderstatus AS ENUM (
            'pending', 'confirmed', 'in_progress', 'sent', 'delivered', 'cancelled'
        )
    """)

    op.execute("""
        CREATE TYPE creationmethod AS ENUM (
            'seller_delivery', 'mobile_client', 'web_client', 'portal_client'
        )
    """)

    # Recreate old tables
    op.create_table(
        'orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('seller_id', sa.UUID(), nullable=False),
        sa.Column('deliver_id', sa.UUID(), nullable=False),
        sa.Column('route_id', sa.UUID(), nullable=False),
        sa.Column('order_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'in_progress', 'sent', 'delivered', 'cancelled', name='orderstatus'), nullable=False),
        sa.Column('destination_address', sa.String(500), nullable=False),
        sa.Column('creation_method', sa.Enum('seller_delivery', 'mobile_client', 'web_client', 'portal_client', name='creationmethod'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'order_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('inventory_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id')
    )
