"""
Script to initialize Repair Execution tables and add sample data.
"""

from sqlalchemy import inspect
from database import engine, SessionLocal
from models import RepairExecution, RepairExecutionStatus


def init_repair_execution_tables():
    """Create repair execution tables if they don't exist"""
    
    # Create tables
    from models.admin import RepairExecution, RepairExecutionStatus
    RepairExecution.__table__.create(engine, checkfirst=True)
    RepairExecutionStatus.__table__.create(engine, checkfirst=True)
    
    print("✓ Repair Execution tables created")


def seed_repair_executions():
    """Add sample repair execution data"""
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(RepairExecution).count()
        if existing > 0:
            print(f"Repair executions already exist ({existing} records)")
            return
        
        # Sample repair execution workflows
        repairs = [
            {
                "name": "Standard Repair",
                "description": "Basic repair process for standard defects",
                "statuses": [
                    {"status": "Intake", "description": "Unit received and logged", "order": 1},
                    {"status": "Diagnosis", "description": "Initial inspection and diagnosis", "order": 2},
                    {"status": "Parts Ordered", "description": "Replacement parts on order", "order": 3},
                    {"status": "In Repair", "description": "Unit is being repaired", "order": 4},
                    {"status": "Testing", "description": "Unit testing in progress", "order": 5},
                    {"status": "Ready for Delivery", "description": "Unit ready to ship back", "order": 6},
                ]
            },
            {
                "name": "Complex Repair",
                "description": "Complex repair process for major defects",
                "statuses": [
                    {"status": "Intake", "description": "Unit received and logged", "order": 1},
                    {"status": "Full Diagnosis", "description": "Comprehensive system diagnosis", "order": 2},
                    {"status": "Engineering Review", "description": "Engineering team assessment", "order": 3},
                    {"status": "Parts Procurement", "description": "Sourcing special components", "order": 4},
                    {"status": "Bench Work", "description": "Component-level repair work", "order": 5},
                    {"status": "Integration", "description": "System integration and assembly", "order": 6},
                    {"status": "System Testing", "description": "Full system validation", "order": 7},
                    {"status": "Field Validation", "description": "Final field testing", "order": 8},
                    {"status": "Ready for Delivery", "description": "Unit certified and ready", "order": 9},
                ]
            },
            {
                "name": "Warranty Repair",
                "description": "Expedited warranty repair process",
                "statuses": [
                    {"status": "Warranty Check", "description": "Verify warranty status", "order": 1},
                    {"status": "Quick Diagnosis", "description": "Fast fault identification", "order": 2},
                    {"status": "Expedited Repair", "description": "Priority repair work", "order": 3},
                    {"status": "Quality Check", "description": "Quality assurance", "order": 4},
                    {"status": "Ready for Delivery", "description": "Unit ready to return", "order": 5},
                ]
            },
            {
                "name": "Refurbishment",
                "description": "Complete unit refurbishment process",
                "statuses": [
                    {"status": "Intake", "description": "Unit received", "order": 1},
                    {"status": "Cleaning", "description": "Unit cleaning and preparation", "order": 2},
                    {"status": "Component Testing", "description": "All components tested", "order": 3},
                    {"status": "Replacement", "description": "Defective components replaced", "order": 4},
                    {"status": "Recalibration", "description": "System recalibration", "order": 5},
                    {"status": "Full System Test", "description": "Complete system validation", "order": 6},
                    {"status": "Documentation", "description": "Service documentation prepared", "order": 7},
                    {"status": "Ready for Delivery", "description": "Refurbished unit ready", "order": 8},
                ]
            },
        ]
        
        for repair_data in repairs:
            repair = RepairExecution(
                name=repair_data["name"],
                description=repair_data["description"]
            )
            db.add(repair)
            db.flush()  # Get the ID
            
            # Add statuses
            for status_data in repair_data["statuses"]:
                status = RepairExecutionStatus(
                    repair_execution_id=repair.id,
                    status=status_data["status"],
                    description=status_data["description"],
                    order=status_data["order"]
                )
                db.add(status)
        
        db.commit()
        total_executions = db.query(RepairExecution).count()
        total_statuses = db.query(RepairExecutionStatus).count()
        print(f"✓ Added {total_executions} repair executions with {total_statuses} total statuses")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding repair executions: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_repair_execution_tables()
    seed_repair_executions()
