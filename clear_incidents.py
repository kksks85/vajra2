"""
Script to clear all incident records from the database.
"""

from database import SessionLocal
from models import Incident

def clear_incidents():
    """Delete all incident records"""
    
    db = SessionLocal()
    
    try:
        # Get count before deletion
        count = db.query(Incident).count()
        print(f"Found {count} incident records to delete...")
        
        # Delete all incidents
        db.query(Incident).delete()
        db.commit()
        
        # Verify deletion
        remaining = db.query(Incident).count()
        print(f"✓ Successfully deleted all {count} incident records")
        print(f"Remaining incidents: {remaining}")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error clearing incidents: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_incidents()
