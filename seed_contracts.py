"""
Seed script to create sample contracts with various scenarios
"""
from datetime import datetime, timedelta
from database import SessionLocal
from models.entities import Contract, Customer

def seed_contracts():
    db = SessionLocal()
    
    # Get all customers
    customers = db.query(Customer).all()
    
    if not customers:
        print("No customers found. Please run seed_customers.py first.")
        db.close()
        return
    
    # Check if contracts already exist
    existing_contracts = db.query(Contract).count()
    if existing_contracts > 0:
        print(f"Contracts already exist ({existing_contracts}). Skipping seeding.")
        db.close()
        return
    
    today = datetime.now().date()
    
    contracts_data = []
    
    # ===== INDIAN AIR FORCE (Customer 1) =====
    # Contract 1: Active - Under Warranty (With Spares)
    contracts_data.append({
        "number": "IAF-CONTRACT-2024-001",
        "customer_id": customers[0].id,
        "data": {
            "executed_on": (today - timedelta(days=90)).isoformat(),
            "valid_till": (today + timedelta(days=270)).isoformat(),
            "status": "Active - Under Warranty",
            "attachment": None,
            "main_deliverables": [
                {"product": "Loitering Munition", "quantity": "5"},
                {"product": "GCS", "quantity": "2"}
            ],
            "main_warranty": True,
            "main_manuals": "Version 2.1 (Issued: 2024-01-15), Version 2.0 (Issued: 2023-12-01)",
            "scheduled_maintenance": True,
            "unscheduled_maintenance": True,
            "calibration": True,
            "software_upgrade": True,
            "visits": "5 visits completed, 12 personnel days",
            "refresher_training": True,
            "spares": [
                {
                    "name": "Power Supply Unit (PSU) 5000W",
                    "part_number": "PSU-LM-5000-V2",
                    "serial_number": "PSU-001-2024",
                    "quantity": "2"
                },
                {
                    "name": "Communication Module",
                    "part_number": "COMM-GCS-001-V3",
                    "serial_number": "COMM-001-2024",
                    "quantity": "1"
                }
            ]
        }
    })
    
    # Contract 2: Active - Under AMC (Warranty Expired) (With Spares)
    contracts_data.append({
        "number": "IAF-CONTRACT-2023-002",
        "customer_id": customers[0].id,
        "data": {
            "executed_on": (today - timedelta(days=400)).isoformat(),
            "valid_till": (today + timedelta(days=100)).isoformat(),
            "status": "Active - Under AMC (Warranty Expired)",
            "attachment": None,
            "main_deliverables": [
                {"product": "Simulator", "quantity": "1"}
            ],
            "main_warranty": False,
            "main_manuals": "Version 1.8 (Issued: 2023-03-10)",
            "scheduled_maintenance": True,
            "unscheduled_maintenance": True,
            "calibration": False,
            "software_upgrade": False,
            "visits": "8 visits completed, 18 personnel days",
            "refresher_training": False,
            "spares": [
                {
                    "name": "Display Screen 4K",
                    "part_number": "DISP-SIM-4K-V1",
                    "serial_number": "DISP-002-2024",
                    "quantity": "1"
                }
            ]
        }
    })
    
    # Contract 3: Warranty Expired No AMC / CMC (Without Spares)
    contracts_data.append({
        "number": "IAF-CONTRACT-2022-003",
        "customer_id": customers[0].id,
        "data": {
            "executed_on": (today - timedelta(days=730)).isoformat(),
            "valid_till": (today - timedelta(days=100)).isoformat(),
            "status": "Warranty Expired No AMC / CMC",
            "attachment": None,
            "main_deliverables": [
                {"product": "RDV", "quantity": "2"}
            ],
            "main_warranty": False,
            "main_manuals": "Version 1.5 (Issued: 2022-06-20)",
            "scheduled_maintenance": False,
            "unscheduled_maintenance": False,
            "calibration": False,
            "software_upgrade": False,
            "visits": "10 visits completed, 22 personnel days",
            "refresher_training": False,
            "spares": []
        }
    })
    
    # ===== INDIAN ARMY (Customer 2) =====
    # Contract 1: Active - Under Warranty (Without Spares)
    contracts_data.append({
        "number": "IA-CONTRACT-2024-001",
        "customer_id": customers[1].id,
        "data": {
            "executed_on": (today - timedelta(days=60)).isoformat(),
            "valid_till": (today + timedelta(days=300)).isoformat(),
            "status": "Active - Under Warranty",
            "attachment": None,
            "main_deliverables": [
                {"product": "GCS", "quantity": "3"},
                {"product": "Loitering Munition", "quantity": "10"}
            ],
            "main_warranty": True,
            "main_manuals": "Version 3.0 (Issued: 2024-02-01), Version 2.9 (Issued: 2024-01-10)",
            "scheduled_maintenance": True,
            "unscheduled_maintenance": True,
            "calibration": True,
            "software_upgrade": True,
            "visits": "3 visits completed, 8 personnel days",
            "refresher_training": True,
            "spares": []
        }
    })
    
    # Contract 2: Active - Under CMC (Warranty Expired) (With Spares)
    contracts_data.append({
        "number": "IA-CONTRACT-2023-002",
        "customer_id": customers[1].id,
        "data": {
            "executed_on": (today - timedelta(days=450)).isoformat(),
            "valid_till": (today + timedelta(days=150)).isoformat(),
            "status": "Active - Under CMC (Warranty Expired)",
            "attachment": None,
            "main_deliverables": [
                {"product": "TMV", "quantity": "2"},
                {"product": "Simulator", "quantity": "1"}
            ],
            "main_warranty": False,
            "main_manuals": "Version 2.0 (Issued: 2023-05-15)",
            "scheduled_maintenance": False,
            "unscheduled_maintenance": True,
            "calibration": True,
            "software_upgrade": True,
            "visits": "6 visits completed, 14 personnel days",
            "refresher_training": False,
            "spares": [
                {
                    "name": "Engine Control Unit",
                    "part_number": "ECU-TMV-500-V2",
                    "serial_number": "ECU-003-2024",
                    "quantity": "1"
                },
                {
                    "name": "Hydraulic Pump",
                    "part_number": "HYDR-PUMP-200-V1",
                    "serial_number": "HYDR-004-2024",
                    "quantity": "2"
                },
                {
                    "name": "Battery Pack",
                    "part_number": "BATT-PACK-48V",
                    "serial_number": "BATT-005-2024",
                    "quantity": "3"
                }
            ]
        }
    })
    
    # Contract 3: Warranty Expired No AMC / CMC (With Spares)
    contracts_data.append({
        "number": "IA-CONTRACT-2021-003",
        "customer_id": customers[1].id,
        "data": {
            "executed_on": (today - timedelta(days=900)).isoformat(),
            "valid_till": (today - timedelta(days=200)).isoformat(),
            "status": "Warranty Expired No AMC / CMC",
            "attachment": None,
            "main_deliverables": [
                {"product": "RDV", "quantity": "1"}
            ],
            "main_warranty": False,
            "main_manuals": "Version 1.4 (Issued: 2021-08-12)",
            "scheduled_maintenance": False,
            "unscheduled_maintenance": False,
            "calibration": False,
            "software_upgrade": False,
            "visits": "12 visits completed, 28 personnel days",
            "refresher_training": False,
            "spares": [
                {
                    "name": "Spare Tire Set",
                    "part_number": "TIRE-RDV-OFF-ROAD",
                    "serial_number": "TIRE-006-2024",
                    "quantity": "4"
                }
            ]
        }
    })
    
    # ===== INDIAN NAVY (Customer 3) =====
    # Contract 1: Active - Under Warranty (With Spares)
    contracts_data.append({
        "number": "IN-CONTRACT-2024-001",
        "customer_id": customers[2].id,
        "data": {
            "executed_on": (today - timedelta(days=45)).isoformat(),
            "valid_till": (today + timedelta(days=315)).isoformat(),
            "status": "Active - Under Warranty",
            "attachment": None,
            "main_deliverables": [
                {"product": "Simulator", "quantity": "2"},
                {"product": "GCS", "quantity": "1"}
            ],
            "main_warranty": True,
            "main_manuals": "Version 2.5 (Issued: 2024-02-10)",
            "scheduled_maintenance": True,
            "unscheduled_maintenance": True,
            "calibration": True,
            "software_upgrade": True,
            "visits": "2 visits completed, 5 personnel days",
            "refresher_training": True,
            "spares": [
                {
                    "name": "Network Switch 48-port",
                    "part_number": "SWITCH-NET-48P-V2",
                    "serial_number": "SWITCH-007-2024",
                    "quantity": "1"
                },
                {
                    "name": "Fiber Optic Cable 10km",
                    "part_number": "FIBER-10KM-SM",
                    "serial_number": "FIBER-008-2024",
                    "quantity": "2"
                }
            ]
        }
    })
    
    # Contract 2: Active - Under AMC (Warranty Expired) (Without Spares)
    contracts_data.append({
        "number": "IN-CONTRACT-2023-002",
        "customer_id": customers[2].id,
        "data": {
            "executed_on": (today - timedelta(days=380)).isoformat(),
            "valid_till": (today + timedelta(days=120)).isoformat(),
            "status": "Active - Under AMC (Warranty Expired)",
            "attachment": None,
            "main_deliverables": [
                {"product": "Loitering Munition", "quantity": "8"}
            ],
            "main_warranty": False,
            "main_manuals": "Version 1.9 (Issued: 2023-04-20)",
            "scheduled_maintenance": True,
            "unscheduled_maintenance": True,
            "calibration": False,
            "software_upgrade": False,
            "visits": "7 visits completed, 16 personnel days",
            "refresher_training": False,
            "spares": []
        }
    })
    
    # Contract 3: Warranty Expired No AMC / CMC (With Spares)
    contracts_data.append({
        "number": "IN-CONTRACT-2021-003",
        "customer_id": customers[2].id,
        "data": {
            "executed_on": (today - timedelta(days=850)).isoformat(),
            "valid_till": (today - timedelta(days=150)).isoformat(),
            "status": "Warranty Expired No AMC / CMC",
            "attachment": None,
            "main_deliverables": [
                {"product": "TMV", "quantity": "1"},
                {"product": "RDV", "quantity": "1"}
            ],
            "main_warranty": False,
            "main_manuals": "Version 1.3 (Issued: 2021-07-15)",
            "scheduled_maintenance": False,
            "unscheduled_maintenance": False,
            "calibration": False,
            "software_upgrade": False,
            "visits": "11 visits completed, 25 personnel days",
            "refresher_training": False,
            "spares": [
                {
                    "name": "Brake Pad Set",
                    "part_number": "BRAKE-PAD-PREMIUM",
                    "serial_number": "BRAKE-009-2024",
                    "quantity": "2"
                }
            ]
        }
    })
    
    # Create all contracts
    for contract_data in contracts_data:
        contract = Contract(
            number=contract_data["number"],
            customer_id=contract_data["customer_id"],
            data=contract_data["data"]
        )
        db.add(contract)
    
    db.commit()
    print(f"✅ Successfully created {len(contracts_data)} sample contracts with various scenarios:")
    print("   - 3 contracts per customer (Indian Air Force, Indian Army, Indian Navy)")
    print("   - Each customer has: 1 Active (Warranty), 1 Active (AMC/CMC), 1 Expired contract")
    print("   - Mix of contracts with and without spares")
    print("   - All products and quantities covered")
    
    db.close()

if __name__ == "__main__":
    seed_contracts()
