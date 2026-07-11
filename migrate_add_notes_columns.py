import sqlite3

def migrate():
    """Add work_notes and audit_log columns to incidents table."""
    conn = sqlite3.connect("vajra.db")
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(incidents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "work_notes" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN work_notes TEXT")
            print("work_notes column added successfully")
        else:
            print("work_notes column already exists")
        
        if "audit_log" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN audit_log TEXT")
            print("audit_log column added successfully")
        else:
            print("audit_log column already exists")
        
        conn.commit()
        print("Migration completed successfully!")
    
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
