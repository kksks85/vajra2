import sqlite3

def migrate():
    """Add resolved_by, resolved_date_time, and resolution_notes columns to incidents table."""
    conn = sqlite3.connect("vajra.db")
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(incidents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "resolved_by" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN resolved_by VARCHAR(200)")
            print("resolved_by column added successfully")
        else:
            print("resolved_by column already exists")
            
        if "resolved_date_time" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN resolved_date_time VARCHAR(100)")
            print("resolved_date_time column added successfully")
        else:
            print("resolved_date_time column already exists")
            
        if "resolution_notes" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN resolution_notes TEXT")
            print("resolution_notes column added successfully")
        else:
            print("resolution_notes column already exists")
        
        conn.commit()
        print("Migration completed successfully!")
    
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
