#!/usr/bin/env python
"""
Migration script to add query_number column to query_requests table
"""

import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), "vajra.db")

if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if query_number column already exists
    cursor.execute("PRAGMA table_info(query_requests)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'query_number' in columns:
        print("✓ query_number column already exists")
    else:
        print("Adding query_number column to query_requests table...")
        # Add column without UNIQUE constraint to avoid issues with NULL values
        cursor.execute("ALTER TABLE query_requests ADD COLUMN query_number VARCHAR(50)")
        conn.commit()
        print("✓ Successfully added query_number column")
    
    # Verify the column was added
    cursor.execute("PRAGMA table_info(query_requests)")
    columns = cursor.fetchall()
    print("\nCurrent query_requests columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    print("\n✓ Migration completed successfully!")
    
except sqlite3.Error as e:
    print(f"✗ Database error: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)
