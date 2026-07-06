"""
Seed script to create individual LM (Loitering Munition) units based on contracts
"""
from database import SessionLocal
from models.entities import Contract, LoiteringMunition, Customer
from datetime import datetime, timedelta
import random

def seed_lm_units():
    db = SessionLocal()
    
    try:
        # Check if LM units already exist
        existing_lm = db.query(LoiteringMunition).count()
        if existing_lm > 0:
            print(f"LM units already exist ({existing_lm} units). Deleting and recreating...")
            db.query(LoiteringMunition).delete()
            db.commit()
        
        # Get all contracts
        contracts = db.query(Contract).all()
        
        lm_count = 0
        today = datetime.now().date()
        
        for contract in contracts:
            # Get deliverables from contract
            deliverables = contract.data.get('main_deliverables', [])
            
            # Count LM units in this contract
            lm_quantity = 0
            for item in deliverables:
                if item.get('product') == 'Loitering Munition':
                    lm_quantity = int(item.get('quantity', 0))
                    break
            
            if lm_quantity > 0:
                # Get customer name from customer table using customer_id
                customer_name = ''
                if contract.customer_id:
                    customer = db.query(Customer).filter(Customer.id == contract.customer_id).first()
                    if customer:
                        customer_name = customer.name
                
                contract_number = contract.number
                
                # Generate realistic warranty dates based on contract status
                contract_status = contract.data.get('status', 'Active')
                if contract_status == 'Active':
                    # Active warranty: 6-24 months from now
                    warranty_days = random.randint(180, 720)
                elif contract_status == 'Active-AMC' or contract_status == 'Active-CMC':
                    # Active maintenance: 12-36 months from now
                    warranty_days = random.randint(365, 1095)
                elif contract_status == 'Warranty Expired':
                    # Expired: already past
                    warranty_days = random.randint(-90, -1)
                else:
                    # Default: 6-12 months from now
                    warranty_days = random.randint(180, 365)
                
                warranty_valid_to_date = today + timedelta(days=warranty_days)
                warranty_valid_to = warranty_valid_to_date.strftime("%Y-%m-%d")
                warranty_valid_from_date = today - timedelta(days=365)  # 1 year back
                warranty_valid_from = warranty_valid_from_date.strftime("%Y-%m-%d")
                
                # Update contract's main_deliverables to include warranty info per product
                updated_deliverables = []
                for item in deliverables:
                    if item.get('product') == 'Loitering Munition':
                        item['warranty_valid_to'] = warranty_valid_to
                        item['warranty_valid_from'] = warranty_valid_from
                    updated_deliverables.append(item)
                
                # Update contract with warranty dates
                contract_data = contract.data or {}
                contract_data['main_deliverables'] = updated_deliverables
                contract.data = contract_data
                db.add(contract)
                
                # Create individual LM units
                for i in range(1, lm_quantity + 1):
                    # Global LM counter for unique SAP part numbers
                    global_lm_id = lm_count + i
                    
                    # Generate 15-digit SAP part number: 100000000XXXXX
                    sap_part_number = f"{100000000000000 + global_lm_id}"  # 15-digit numeric
                    
                    # Generate realistic service history
                    # Last service: random date in past 3-6 months
                    last_service_days_ago = random.randint(90, 180)
                    last_service_date = today - timedelta(days=last_service_days_ago)
                    last_service_on = last_service_date.strftime("%d-%m-%Y")
                    
                    # Next service: 30-90 days from now (some past due, some upcoming)
                    next_service_days = random.randint(-15, 90)  # -15 to 90 days means some are past due
                    next_service_date = today + timedelta(days=next_service_days)
                    next_service_due = next_service_date.strftime("%d-%m-%Y")
                    
                    # Service notes
                    service_statuses = [
                        "Routine maintenance completed. All systems operational.",
                        "Preventive maintenance. Battery replaced. Software updated.",
                        "Annual inspection. Minor repairs performed.",
                        "Quarterly service. Calibration verified.",
                        "Emergency maintenance. Guidance system repaired.",
                    ]
                    service_notes = random.choice(service_statuses)
                    
                    lm_unit = LoiteringMunition()
                    lm_unit.unit_name = f'LM-{contract.id}-{i}'
                    lm_unit.serial_number = f'LM-SN-{contract.id:03d}-{i:02d}'
                    lm_unit.data = {
                        'sap_part_number': sap_part_number,
                        'customer_part_number': f'CUST-LM-{contract.id}-{i}',
                        'customer': customer_name,
                        'contract': contract_number,
                        'warranty_valid_from': warranty_valid_from,
                        'warranty_valid_to': warranty_valid_to,
                        'make': 'Vajra Defense',
                        'model': f'LM-{i}',
                        'software_version': '2.0',
                        'status': 'Active',
                        'contract_id': contract.id,
                        'last_service_on': last_service_on,
                        'next_service_due': next_service_due,
                        'service_notes': service_notes
                    }
                    db.add(lm_unit)
                    lm_count += 1
        
        db.commit()
        print(f"✅ Successfully created {lm_count} LM units from {len(contracts)} contracts")
        print(f"✅ Warranty dates seeded with realistic values")
        print(f"✅ Contract main_deliverables updated with warranty information")
        print(f"✅ All SAP part numbers set to 15-digit numeric format (100000000000001 - 100000000000023)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding LM units: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    seed_lm_units()
