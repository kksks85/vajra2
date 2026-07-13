import sqlite3

def migrate():
    """Create the reports table in the database."""
    conn = sqlite3.connect("vajra.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                description VARCHAR(500) DEFAULT '',
                data_source VARCHAR(100) NOT NULL,
                chart_type VARCHAR(50) NOT NULL,
                x_field VARCHAR(100) NOT NULL,
                y_field VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """)
        print("reports table created successfully")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating reports table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
