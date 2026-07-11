"""
Drop and recreate repair execution tables
"""

from sqlalchemy import inspect, text
from database import engine, SessionLocal, Base
from models.admin import RepairExecution, RepairExecutionStatus

def drop_and_recreate():
    """Drop existing tables and recreate them"""
    
    try:
        # Drop tables if they exist
        Base.metadata.drop_all(bind=engine, tables=[RepairExecutionStatus.__table__, RepairExecution.__table__])
        print("✓ Dropped existing tables")
        
        # Create new tables
        RepairExecution.__table__.create(bind=engine, checkfirst=True)
        RepairExecutionStatus.__table__.create(bind=engine, checkfirst=True)
        print("✓ Created new tables")
        
        # Seed sample data
        db = SessionLocal()
        
        sample_data = [
            ("Standard Repair", "Initial Inspection", 1),
            ("Standard Repair", "Diagnosis", 2),
            ("Standard Repair", "Repair", 3),
            ("Standard Repair", "Testing", 4),
            ("Standard Repair", "Quality Check", 5),
            ("Standard Repair", "Dispatch", 6),
            ("Complex Repair", "Detailed Analysis", 1),
            ("Complex Repair", "Component Testing", 2),
            ("Complex Repair", "Major Repair", 3),
            ("Complex Repair", "System Integration", 4),
            ("Complex Repair", "Performance Testing", 5),
            ("Complex Repair", "Documentation", 6),
            ("Complex Repair", "Final Inspection", 7),
            ("Complex Repair", "Certification", 8),
            ("Complex Repair", "Handover", 9),
            ("Warranty Repair", "Warranty Verification", 1),
            ("Warranty Repair", "Expedited Diagnosis", 2),
            ("Warranty Repair", "Quick Repair", 3),
            ("Warranty Repair", "Verification", 4),
            ("Warranty Repair", "Customer Return", 5),
            ("Refurbishment", "Complete Teardown", 1),
            ("Refurbishment", "Component Cleaning", 2),
            ("Refurbishment", "Component Inspection", 3),
            ("Refurbishment", "Component Replacement", 4),
            ("Refurbishment", "Reassembly", 5),
            ("Refurbishment", "Calibration", 6),
            ("Refurbishment", "Quality Testing", 7),
            ("Refurbishment", "Final Inspection", 8),
        ]
        
        for repair_execution, status, order in sample_data:
            item = RepairExecution(
                repair_execution=repair_execution,
                status=status,
                order=order
            )
            db.add(item)
        
        db.commit()
        print(f"✓ Seeded {len(sample_data)} sample records")
        db.close()
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        raise

if __name__ == "__main__":
    drop_and_recreate()
