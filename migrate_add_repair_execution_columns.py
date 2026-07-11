import sqlite3
import os
from datetime import datetime

# Path to the database
DB_PATH = "vajra.db"

def migrate():
    """Add repair_execution and repair_status columns to incidents table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(incidents)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'repair_execution' not in columns:
            print("Adding repair_execution column...")
            cursor.execute("""
                ALTER TABLE incidents 
                ADD COLUMN repair_execution VARCHAR(100)
            """)
        else:
            print("repair_execution column already exists")
        
        if 'repair_status' not in columns:
            print("Adding repair_status column...")
            cursor.execute("""
                ALTER TABLE incidents 
                ADD COLUMN repair_status VARCHAR(200)
            """)
        else:
            print("repair_status column already exists")
        
        if 'repair_execution_status' not in columns:
            print("Adding repair_execution_status column...")
            cursor.execute("""
                ALTER TABLE incidents 
                ADD COLUMN repair_execution_status VARCHAR(200)
            """)
        else:
            print("repair_execution_status column already exists")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        migrate()
    else:
        print(f"Database file not found at {DB_PATH}")
