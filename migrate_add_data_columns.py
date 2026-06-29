#!/usr/bin/env python
"""
Script to add missing columns to tables that need them.
This handles the schema migration dynamically without recreating the database.
"""
import sys
from sqlalchemy import text, inspect
from database import engine, Base

# Import all models to ensure metadata is populated
import models.admin
import models.entities
import models.incident
import models.knowledge
import models.lowcode

# Set output encoding to UTF-8 to prevent console issues on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def migrate_schema():
    """Dynamically find and add any missing columns in the database."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print("Starting database schema migration check...\n")
    
    migrated_columns_count = 0
    checked_tables_count = 0
    
    with engine.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            if table_name not in existing_tables:
                print(f"[INFO] Table '{table_name}' does not exist in DB yet. (Will be created on next app startup)")
                continue
            
            checked_tables_count += 1
            # Get columns from DB
            db_columns = {col['name']: col for col in inspector.get_columns(table_name)}
            
            # Check each column in the model
            for column in table.columns:
                if column.name not in db_columns:
                    print(f"[MIGRATE] Table '{table_name}': column '{column.name}' is missing in database.")
                    
                    # Build ALTER TABLE SQL
                    col_type_str = str(column.type)
                    
                    # Determine SQLite type and default value
                    if 'JSON' in col_type_str:
                        col_type = 'JSON'
                        default_val = " DEFAULT '{}'"
                    elif 'VARCHAR' in col_type_str or 'String' in col_type_str:
                        col_type = col_type_str
                        default_val = " DEFAULT ''"
                    elif 'INTEGER' in col_type_str or 'Integer' in col_type_str:
                        col_type = 'INTEGER'
                        default_val = " DEFAULT 0"
                    elif 'BOOLEAN' in col_type_str or 'Boolean' in col_type_str:
                        col_type = 'BOOLEAN'
                        default_val = " DEFAULT 1"
                    else:
                        col_type = col_type_str
                        default_val = ""
                    
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}{default_val}"
                    print(f"Executing: {sql}")
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✓ Added column '{column.name}' to '{table_name}'")
                        migrated_columns_count += 1
                    except Exception as e:
                        print(f"✗ Failed to add column '{column.name}' to '{table_name}': {e}")
                        
    print(f"\nMigration check complete! Checked {checked_tables_count} tables. Added {migrated_columns_count} columns.")

if __name__ == "__main__":
    migrate_schema()

