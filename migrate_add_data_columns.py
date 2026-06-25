#!/usr/bin/env python
"""
Script to add missing 'data' columns to tables that need them.
This handles the schema migration without recreating the database.
"""
from sqlalchemy import text, inspect
from database import engine

def add_column_if_missing(table_name, column_name, column_type):
    """Add a column to a table if it doesn't already exist."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column_name in columns:
        print(f"✓ Column '{column_name}' already exists in '{table_name}'")
        return True
    
    try:
        with engine.connect() as conn:
            if engine.dialect.name == 'sqlite':
                # SQLite syntax
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{{}}'"
            else:
                # MySQL/PostgreSQL syntax
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{{}}'"
            
            conn.execute(text(sql))
            conn.commit()
            print(f"✓ Added column '{column_name}' to '{table_name}'")
            return True
    except Exception as e:
        print(f"✗ Failed to add column '{column_name}' to '{table_name}': {e}")
        return False

def main():
    """Add missing data columns to tables."""
    tables_to_update = [
        ('groups', 'data', 'JSON'),
        ('knowledge_documents', 'data', 'JSON'),
        ('workflows', 'data', 'JSON'),
        ('stages', 'data', 'JSON'),
        ('task_definitions', 'data', 'JSON'),
    ]
    
    print("Starting migration to add missing 'data' columns...\n")
    
    success_count = 0
    for table_name, column_name, column_type in tables_to_update:
        if add_column_if_missing(table_name, column_name, column_type):
            success_count += 1
    
    print(f"\nMigration complete! Updated {success_count}/{len(tables_to_update)} tables.")

if __name__ == "__main__":
    main()
