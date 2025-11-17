#!/usr/bin/env python3
"""Reset staging databases - drop all tables."""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Staging RDS connection
RDS_HOST = "medisupply-staging-medisupply.c27e88m4y9tb.us-east-1.rds.amazonaws.com"
RDS_USER = "postgres"
RDS_PASSWORD = "Password123"
RDS_PORT = "5432"

# Database names (assuming one database per service)
DATABASES = [
    "medisupply_order",
    "medisupply_catalog",
    "medisupply_client",
    "medisupply_inventory",
    "medisupply_seller"
]

# Also try the main database
DATABASES_ALTERNATIVE = ["medisupply"]


def drop_all_tables(db_name):
    """Drop all tables from a database."""
    print(f"\n{'='*60}")
    print(f"Processing database: {db_name}")
    print(f"{'='*60}")

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            port=RDS_PORT,
            database=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()

        if not tables:
            print(f"✓ No tables found in {db_name}")
        else:
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")

            # Drop all tables
            print(f"\nDropping all tables...")
            for table in tables:
                table_name = table[0]
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
                print(f"  ✓ Dropped: {table_name}")

            print(f"\n✅ All tables dropped from {db_name}")

        cursor.close()
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        if "database" in str(e) and "does not exist" in str(e):
            print(f"⚠️  Database {db_name} does not exist - skipping")
            return False
        else:
            print(f"❌ Error connecting to {db_name}: {e}")
            return False
    except Exception as e:
        print(f"❌ Error processing {db_name}: {e}")
        return False


def list_all_databases():
    """List all databases to find the correct names."""
    print(f"\n{'='*60}")
    print("Listing all databases on staging RDS")
    print(f"{'='*60}")

    try:
        conn = psycopg2.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            port=RDS_PORT,
            database="postgres"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = cursor.fetchall()

        print("\nAvailable databases:")
        for db in databases:
            print(f"  - {db[0]}")

        cursor.close()
        conn.close()
        return [db[0] for db in databases]

    except Exception as e:
        print(f"❌ Error listing databases: {e}")
        return []


if __name__ == "__main__":
    print("🚀 STAGING DATABASE RESET SCRIPT")
    print(f"Host: {RDS_HOST}")
    print(f"User: {RDS_USER}")

    # First, list all databases
    all_dbs = list_all_databases()

    # Filter for medisupply databases
    medisupply_dbs = [db for db in all_dbs if 'medisupply' in db.lower()]

    if not medisupply_dbs:
        print("\n⚠️  No medisupply databases found!")
        print("Trying default list...")
        medisupply_dbs = DATABASES + DATABASES_ALTERNATIVE

    print(f"\n\nWill process {len(medisupply_dbs)} database(s):")
    for db in medisupply_dbs:
        print(f"  - {db}")

    # Process each database
    for db_name in medisupply_dbs:
        drop_all_tables(db_name)

    print(f"\n{'='*60}")
    print("✅ DONE - All staging databases processed")
    print(f"{'='*60}")
