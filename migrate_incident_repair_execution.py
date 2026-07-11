#!/usr/bin/env python3
"""
Migration script to update Incident table for new Repair Execution schema
Changes repair_execution_status_id (FK) to repair_execution_status (String)
"""

from sqlalchemy import Column, String, inspect
from database import engine
from models.incident import Base, Incident
import sys

def migrate():
    """Run the migration"""
    try:
        inspector = inspect(engine)
        incident_columns = inspector.get_columns('incidents')
        
        # Check if the column already exists
        column_names = [col['name'] for col in incident_columns]
        
        print("Current columns in incidents table:")
        for col in incident_columns:
            print(f"  - {col['name']}: {col['type']}")
        
        if 'repair_execution_status_id' in column_names:
            print("\nMigrating from repair_execution_status_id to repair_execution_status...")
            
            # SQLite doesn't support direct column removal/renaming in all versions
            # We'll need to recreate the table
            with engine.connect() as conn:
                # Create backup
                conn.execute("CREATE TABLE incidents_backup AS SELECT * FROM incidents")
                conn.commit()
                
                # Drop the old table
                conn.execute("DROP TABLE incidents")
                conn.commit()
                
            # Create the new table with updated schema
            Base.metadata.create_all(engine)
            
            print("✓ Migration complete - table recreated with new schema")
            print("  Old incidents data has been backed up to 'incidents_backup' table")
            
        elif 'repair_execution_status' in column_names:
            print("✓ Migration not needed - repair_execution_status column already exists")
        else:
            print("! Warning: Neither repair_execution_status_id nor repair_execution_status found")
            print("  Running table creation to ensure schema exists...")
            Base.metadata.create_all(engine)
            
    except Exception as e:
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    print("Starting Incident table migration...\n")
    migrate()
    print("\n✓ All migrations completed successfully!")
