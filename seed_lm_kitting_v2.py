"""
Seed script to populate LM Kitting materials organized by route cards and sub-systems
Each LM has materials under each route card with max quantity of 1 per item
"""
from database import SessionLocal
from models.entities import LoiteringMunition, KittingItem
import random
import string

# Route Cards with their sub-systems
ROUTE_CARDS = {
    "LH Side Wing Integration Assembly": [
        "Wing Structure",
        "Control Surfaces",
        "Electrical Integration",
        "Fastening & Hardware"
    ],
    "RH Side Wing Integration Assembly": [
        "Wing Structure",
        "Control Surfaces",
        "Electrical Integration",
        "Fastening & Hardware"
    ],
    "LH Empennage Integration Assembly": [
        "Vertical Stabilizer",
        "Horizontal Stabilizer",
        "Control Surfaces",
        "Fastening & Hardware"
    ],
    "RH Empennage Integration Assembly": [
        "Vertical Stabilizer",
        "Horizontal Stabilizer",
        "Control Surfaces",
        "Fastening & Hardware"
    ],
    "VTOL Boom Bracket Integration Assembly LH": [
        "Boom Structure",
        "Motor Integration",
        "Electrical Connections",
        "Fastening & Hardware"
    ],
    "VTOL Boom Bracket Integration Assembly RH": [
        "Boom Structure",
        "Motor Integration",
        "Electrical Connections",
        "Fastening & Hardware"
    ],
    "Centre Wing Integration Assembly": [
        "Wing Structure",
        "Fuel System Integration",
        "Electrical Integration",
        "Fastening & Hardware"
    ],
    "Fuselage Integration Assembly": [
        "Fuselage Shell",
        "Internal Structures",
        "Avionics Bay",
        "Cable Management",
        "Fastening & Hardware"
    ],
    "Aircraft ERLM Assembly": [
        "Flight Systems",
        "Propulsion System",
        "Engine Assembly",
        "Landing Gear",
        "Avionics Integration",
        "Power Distribution",
        "Fuel System"
    ]
}

# Material templates for different sub-systems
MATERIALS = {
    "Wing Structure": [
        "Carbon Fiber Wing Panel", "Aluminum Spar", "Wing Rib", "Wing Tip",
        "Wing Root Attachment"
    ],
    "Control Surfaces": [
        "Aileron", "Flap", "Elevator", "Rudder", "Control Rod Assembly"
    ],
    "Electrical Integration": [
        "Power Cable", "Signal Wire", "Connector Block", "Terminal Strip",
        "Electrical Harness"
    ],
    "Fastening & Hardware": [
        "Titanium Bolt", "Aluminum Rivet", "Hex Nut", "Washer", "Lock Ring",
        "Quick Release Pin"
    ],
    "Vertical Stabilizer": [
        "Vertical Stabilizer Frame", "Vertical Stabilizer Cover"
    ],
    "Horizontal Stabilizer": [
        "Horizontal Stabilizer Frame", "Horizontal Stabilizer Cover"
    ],
    "Boom Structure": [
        "Carbon Boom Tube", "Boom Connector", "Boom Support Bracket"
    ],
    "Motor Integration": [
        "BLDC Motor", "Motor Mount", "Motor Controller", "Propeller Adapter"
    ],
    "Electrical Connections": [
        "Power Connector", "Signal Connector", "Connector Housing", "Pin Contact"
    ],
    "Fuel System Integration": [
        "Fuel Tank", "Fuel Line", "Fuel Filter", "Fuel Pump"
    ],
    "Fuselage Shell": [
        "Composite Fuselage Panel", "Fuselage Frame", "Nose Cone", "Tail Cone"
    ],
    "Internal Structures": [
        "Internal Support Beam", "Cross Member", "Mounting Plate"
    ],
    "Avionics Bay": [
        "Flight Controller", "GPS Module", "IMU Sensor", "Barometer"
    ],
    "Cable Management": [
        "Cable Tray", "Cable Tie", "Cable Sleeve", "Cable Gland"
    ],
    "Flight Systems": [
        "Flight Controller Board", "Gyroscope Sensor", "Accelerometer", "Altitude Sensor"
    ],
    "Propulsion System": [
        "Fuel Pump Assembly", "Fuel Regulator", "Fuel Injector", "Ignition Coil"
    ],
    "Engine Assembly": [
        "Engine Block", "Crankshaft", "Piston", "Connecting Rod", "Engine Mount"
    ],
    "Landing Gear": [
        "Landing Gear Strut", "Wheel Assembly", "Shock Absorber", "Brake Disc"
    ],
    "Avionics Integration": [
        "Antenna", "Communication Module", "Data Logger", "Telemetry Unit"
    ],
    "Power Distribution": [
        "Power Distribution Board", "Voltage Regulator", "Power Switch", "Fuse Holder"
    ]
}

def generate_part_number():
    """Generate a unique part number"""
    return f"PN-{random.randint(10000, 99999)}-{random.choice(string.ascii_uppercase)}{random.randint(1000, 9999)}"

def generate_serial_number():
    """Generate a unique serial number"""
    timestamp = random.randint(100000, 999999)
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SN-{timestamp}-{suffix}"

def seed_lm_kitting():
    db = SessionLocal()
    
    try:
        # Check if kitting items already exist
        existing_kitting = db.query(KittingItem).count()
        if existing_kitting > 0:
            print(f"LM Kitting items already exist ({existing_kitting} items). Deleting to reseed...")
            db.query(KittingItem).delete()
            db.commit()
        
        # Get all LM units
        lm_units = db.query(LoiteringMunition).order_by(LoiteringMunition.id).all()
        
        if not lm_units:
            print("No LM units found. Please seed LM units first.")
            return
        
        total_items = 0
        
        # For each LM unit
        for lm in lm_units:
            lm_name = lm.unit_name or f"LM-{lm.id}"
            lm_serial = lm.serial_number or f"LM-SN-{lm.id:03d}-01"
            print(f"Seeding kitting items for {lm_name}...")
            
            # For each route card
            for route_card, sub_systems in ROUTE_CARDS.items():
                # For each sub-system in the route card
                for sub_system in sub_systems:
                    # Get materials for this sub-system
                    materials = MATERIALS.get(sub_system, [])
                    
                    # Add 2-4 materials per sub-system
                    num_materials = random.randint(2, 4)
                    selected_materials = random.sample(materials, min(num_materials, len(materials)))
                    
                    for material in selected_materials:
                        kitting_item = KittingItem()
                        kitting_item.product_serial_no = lm_serial
                        kitting_item.product_category = "LM"
                        kitting_item.route_card_description = route_card
                        kitting_item.part_number = generate_part_number()
                        kitting_item.sap_part_number = f"SAP-{random.randint(100000, 999999)}"
                        kitting_item.material_description = material
                        kitting_item.material_serial_no = generate_serial_number()
                        kitting_item.batch_no_po_no = f"BATCH-{random.randint(1000, 9999)}"
                        kitting_item.weight_in_grams = str(random.randint(10, 5000))
                        kitting_item.required_quantity = "1"
                        kitting_item.uom = "Piece"
                        kitting_item.subsystems = sub_system
                        kitting_item.remarks = f"Standard component for {material}"
                        
                        db.add(kitting_item)
                        total_items += 1
        
        db.commit()
        print(f"\n✅ Successfully seeded {total_items} kitting items for {len(lm_units)} LM units")
        print(f"   Average items per LM: {total_items // len(lm_units)}")
        print(f"   Route cards per LM: 9")
        print(f"   Total route cards: {9 * len(lm_units)}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding LM kitting items: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    seed_lm_kitting()
