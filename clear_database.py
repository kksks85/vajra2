"""
Script to clear all records from the database while keeping the tables structure intact.
"""

from sqlalchemy import inspect, delete
from database import engine, SessionLocal
from models import (
    Incident,
    KnowledgeArticle,
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    ApprovalRequest,
    Role,
    User,
    Customer,
    Contract,
    BatteryType,
    Battery,
    LoiteringMunition,
    GroundControlSystem,
    TacticalMobilityVehicle,
    SimulatorUnit,
    RapidDeploymentVehicle,
    MRLS,
    LineReplaceableUnit,
    SMTSTE,
    SAM,
    SubSystem,
    KittingItem,
    Workflow,
    Stage,
    TaskDefinition,
)


def clear_all_records():
    """Delete all records from all tables"""
    
    db = SessionLocal()
    
    models_to_clear = [
        # Clear in dependency order (dependent tables first)
        Incident,
        KnowledgeDocumentVersion,
        KnowledgeDocument,
        ApprovalRequest,
        KnowledgeArticle,
        Battery,
        BatteryType,
        LoiteringMunition,
        GroundControlSystem,
        TacticalMobilityVehicle,
        SimulatorUnit,
        RapidDeploymentVehicle,
        MRLS,
        LineReplaceableUnit,
        SMTSTE,
        SAM,
        SubSystem,
        KittingItem,
        Contract,
        Customer,
        Workflow,
        Stage,
        TaskDefinition,
        User,
        Role,
    ]
    
    try:
        for model in models_to_clear:
            print(f"Clearing {model.__tablename__}...", end=" ")
            count = db.query(model).delete()
            db.commit()
            print(f"✓ Deleted {count} records")
        
        print("\n✓ All records have been successfully cleared from the database!")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error clearing database: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE CLEAR UTILITY")
    print("=" * 60)
    print("\nThis will DELETE ALL RECORDS from the database.")
    print("The table structures will be preserved.")
    
    response = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
    
    if response.lower() == "yes":
        clear_all_records()
    else:
        print("Operation cancelled.")
