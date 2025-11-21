"""initial_delivery_tables

Revision ID: 001
Revises:
Create Date: 2025-11-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vehicles table
    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("placa", sa.String(20), nullable=False),
        sa.Column("driver_name", sa.String(100), nullable=False),
        sa.Column("driver_phone", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicles_placa"), "vehicles", ["placa"], unique=True)
    op.create_index(op.f("ix_vehicles_is_active"), "vehicles", ["is_active"], unique=False)

    # Create routes table
    op.create_table(
        "routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha_ruta", sa.Date(), nullable=False),
        sa.Column("estado_ruta", sa.String(30), nullable=False, default="planeada"),
        sa.Column("duracion_estimada_minutos", sa.Integer(), nullable=False, default=0),
        sa.Column("total_distance_km", sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column("total_orders", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_routes_vehicle_id"), "routes", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_routes_fecha_ruta"), "routes", ["fecha_ruta"], unique=False)
    op.create_index(op.f("ix_routes_estado_ruta"), "routes", ["estado_ruta"], unique=False)

    # Create shipments table
    op.create_table(
        "shipments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direccion_entrega", sa.String(500), nullable=False),
        sa.Column("ciudad_entrega", sa.String(100), nullable=False),
        sa.Column("pais_entrega", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 8), nullable=True),
        sa.Column("longitude", sa.Numeric(11, 8), nullable=True),
        sa.Column("geocoding_status", sa.String(20), nullable=False, default="pending"),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sequence_in_route", sa.Integer(), nullable=True),
        sa.Column("fecha_pedido", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_entrega_estimada", sa.Date(), nullable=False),
        sa.Column("shipment_status", sa.String(30), nullable=False, default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shipments_order_id"), "shipments", ["order_id"], unique=True)
    op.create_index(op.f("ix_shipments_customer_id"), "shipments", ["customer_id"], unique=False)
    op.create_index(op.f("ix_shipments_geocoding_status"), "shipments", ["geocoding_status"], unique=False)
    op.create_index(op.f("ix_shipments_route_id"), "shipments", ["route_id"], unique=False)
    op.create_index(op.f("ix_shipments_fecha_entrega_estimada"), "shipments", ["fecha_entrega_estimada"], unique=False)
    op.create_index(op.f("ix_shipments_shipment_status"), "shipments", ["shipment_status"], unique=False)

    # Create processed_events table
    op.create_table(
        "processed_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_processed_events_event_id"), "processed_events", ["event_id"], unique=True)
    op.create_index(op.f("ix_processed_events_event_type"), "processed_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_processed_events_event_type"), table_name="processed_events")
    op.drop_index(op.f("ix_processed_events_event_id"), table_name="processed_events")
    op.drop_table("processed_events")

    op.drop_index(op.f("ix_shipments_shipment_status"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_fecha_entrega_estimada"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_route_id"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_geocoding_status"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_customer_id"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_order_id"), table_name="shipments")
    op.drop_table("shipments")

    op.drop_index(op.f("ix_routes_estado_ruta"), table_name="routes")
    op.drop_index(op.f("ix_routes_fecha_ruta"), table_name="routes")
    op.drop_index(op.f("ix_routes_vehicle_id"), table_name="routes")
    op.drop_table("routes")

    op.drop_index(op.f("ix_vehicles_is_active"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_placa"), table_name="vehicles")
    op.drop_table("vehicles")
