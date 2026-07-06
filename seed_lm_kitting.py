"""
Seed script to create LM Kitting materials organized by route cards and sub-assemblies
Materials are categorized and linked to LM units
"""
from database import SessionLocal
from models.entities import KittingItem, LoiteringMunition

# Define route cards and their sub-assemblies with materials
ROUTE_CARDS_MATERIALS = {
    "LH Side Wing Integration Assembly": {
        "sub_assemblies": [
            {
                "name": "Wing Structure",
                "materials": [
                    {"description": "Carbon Fiber Wing Panel LH", "sap": "SAP-CF-WING-LH-01", "category": "Composite"},
                    {"description": "Aluminum Wing Spar LH", "sap": "SAP-AL-SPAR-LH-01", "category": "Structural"},
                    {"description": "Wing Attachment Bracket LH", "sap": "SAP-BR-ATTACH-LH-01", "category": "Hardware"},
                ]
            },
            {
                "name": "Control Surfaces",
                "materials": [
                    {"description": "Aileron Assembly LH", "sap": "SAP-AILERON-LH-01", "category": "Control Surface"},
                    {"description": "Aileron Actuator LH", "sap": "SAP-ACT-AILERON-LH-01", "category": "Actuator"},
                    {"description": "Control Rod Assembly LH", "sap": "SAP-CTRL-ROD-LH-01", "category": "Control Linkage"},
                ]
            },
            {
                "name": "Electrical Integration",
                "materials": [
                    {"description": "Wing Wiring Harness LH", "sap": "SAP-WIRE-WING-LH-01", "category": "Electrical"},
                    {"description": "LED Navigation Light LH", "sap": "SAP-LED-NAV-LH-01", "category": "Lighting"},
                ]
            }
        ]
    },
    "RH Side Wing Integration Assembly": {
        "sub_assemblies": [
            {
                "name": "Wing Structure",
                "materials": [
                    {"description": "Carbon Fiber Wing Panel RH", "sap": "SAP-CF-WING-RH-01", "category": "Composite"},
                    {"description": "Aluminum Wing Spar RH", "sap": "SAP-AL-SPAR-RH-01", "category": "Structural"},
                    {"description": "Wing Attachment Bracket RH", "sap": "SAP-BR-ATTACH-RH-01", "category": "Hardware"},
                ]
            },
            {
                "name": "Control Surfaces",
                "materials": [
                    {"description": "Aileron Assembly RH", "sap": "SAP-AILERON-RH-01", "category": "Control Surface"},
                    {"description": "Aileron Actuator RH", "sap": "SAP-ACT-AILERON-RH-01", "category": "Actuator"},
                    {"description": "Control Rod Assembly RH", "sap": "SAP-CTRL-ROD-RH-01", "category": "Control Linkage"},
                ]
            },
            {
                "name": "Electrical Integration",
                "materials": [
                    {"description": "Wing Wiring Harness RH", "sap": "SAP-WIRE-WING-RH-01", "category": "Electrical"},
                    {"description": "LED Navigation Light RH", "sap": "SAP-LED-NAV-RH-01", "category": "Lighting"},
                ]
            }
        ]
    },
    "LH Empennage Integration Assembly": {
        "sub_assemblies": [
            {
                "name": "Vertical Stabilizer",
                "materials": [
                    {"description": "Vertical Stabilizer Panel LH", "sap": "SAP-VSTAB-LH-01", "category": "Composite"},
                    {"description": "Rudder Assembly LH", "sap": "SAP-RUDDER-LH-01", "category": "Control Surface"},
                    {"description": "Rudder Actuator LH", "sap": "SAP-ACT-RUDDER-LH-01", "category": "Actuator"},
                ]
            },
            {
                "name": "Horizontal Stabilizer",
                "materials": [
                    {"description": "Horizontal Stabilizer Panel LH", "sap": "SAP-HSTAB-LH-01", "category": "Composite"},
                    {"description": "Elevator Assembly LH", "sap": "SAP-ELEVATOR-LH-01", "category": "Control Surface"},
                    {"description": "Elevator Actuator LH", "sap": "SAP-ACT-ELEV-LH-01", "category": "Actuator"},
                ]
            }
        ]
    },
    "RH Empennage Integration Assembly": {
        "sub_assemblies": [
            {
                "name": "Vertical Stabilizer",
                "materials": [
                    {"description": "Vertical Stabilizer Panel RH", "sap": "SAP-VSTAB-RH-01", "category": "Composite"},
                    {"description": "Rudder Assembly RH", "sap": "SAP-RUDDER-RH-01", "category": "Control Surface"},
                    {"description": "Rudder Actuator RH", "sap": "SAP-ACT-RUDDER-RH-01", "category": "Actuator"},
                ]
            },
            {
                "name": "Horizontal Stabilizer",
                "materials": [
                    {"description": "Horizontal Stabilizer Panel RH", "sap": "SAP-HSTAB-RH-01", "category": "Composite"},
                    {"description": "Elevator Assembly RH", "sap": "SAP-ELEVATOR-RH-01", "category": "Control Surface"},
                    {"description": "Elevator Actuator RH", "sap": "SAP-ACT-ELEV-RH-01", "category": "Actuator"},
                ]
            }
        ]
    },
    "VTOL Boom Bracket Integration Assembly LH": {
        "sub_assemblies": [
            {
                "name": "Boom Structure",
                "materials": [
                    {"description": "Carbon Tube VTOL Boom LH", "sap": "SAP-TUBE-VTOL-LH-01", "category": "Structural"},
                    {"description": "VTOL Boom Bracket LH", "sap": "SAP-BR-VTOL-LH-01", "category": "Hardware"},
                    {"description": "Boom Attachment Hardware", "sap": "SAP-HW-BOOM-LH-01", "category": "Fasteners"},
                ]
            },
            {
                "name": "Motor Integration",
                "materials": [
                    {"description": "VTOL Motor 500W LH", "sap": "SAP-MOTOR-500-LH-01", "category": "Motor"},
                    {"description": "Motor Mount Bracket LH", "sap": "SAP-MOTOR-MOUNT-LH-01", "category": "Hardware"},
                    {"description": "Propeller Assembly LH", "sap": "SAP-PROP-LH-01", "category": "Propulsion"},
                ]
            }
        ]
    },
    "VTOL Boom Bracket Integration Assembly RH": {
        "sub_assemblies": [
            {
                "name": "Boom Structure",
                "materials": [
                    {"description": "Carbon Tube VTOL Boom RH", "sap": "SAP-TUBE-VTOL-RH-01", "category": "Structural"},
                    {"description": "VTOL Boom Bracket RH", "sap": "SAP-BR-VTOL-RH-01", "category": "Hardware"},
                    {"description": "Boom Attachment Hardware", "sap": "SAP-HW-BOOM-RH-01", "category": "Fasteners"},
                ]
            },
            {
                "name": "Motor Integration",
                "materials": [
                    {"description": "VTOL Motor 500W RH", "sap": "SAP-MOTOR-500-RH-01", "category": "Motor"},
                    {"description": "Motor Mount Bracket RH", "sap": "SAP-MOTOR-MOUNT-RH-01", "category": "Hardware"},
                    {"description": "Propeller Assembly RH", "sap": "SAP-PROP-RH-01", "category": "Propulsion"},
                ]
            }
        ]
    },
    "Centre Wing Integration Assembly": {
        "sub_assemblies": [
            {
                "name": "Centre Wing Structure",
                "materials": [
                    {"description": "Centre Wing Panel", "sap": "SAP-CF-WING-CENTRE-01", "category": "Composite"},
                    {"description": "Main Spar Centre", "sap": "SAP-AL-SPAR-CENTRE-01", "category": "Structural"},
                    {"description": "Wing Box Structure", "sap": "SAP-WING-BOX-01", "category": "Structural"},
                ]
            },
            {
                "name": "Fuel System",
                "materials": [
                    {"description": "Fuel Tank Assembly", "sap": "SAP-FUEL-TANK-01", "category": "Fuel System"},
                    {"description": "Fuel Pump Unit", "sap": "SAP-FUEL-PUMP-01", "category": "Fuel System"},
                    {"description": "Fuel Filter Assembly", "sap": "SAP-FUEL-FILTER-01", "category": "Fuel System"},
                ]
            },
            {
                "name": "Power Distribution",
                "materials": [
                    {"description": "Main Power Bus", "sap": "SAP-POWER-BUS-01", "category": "Electrical"},
                    {"description": "Battery Pack 48V 20Ah", "sap": "SAP-BATT-48V-01", "category": "Power"},
                    {"description": "Battery Pack 48V 20Ah (Second Unit)", "sap": "SAP-BATT-48V-01", "category": "Power"},
                    {"description": "Power Supply Unit 5000W", "sap": "SAP-PSU-5000-01", "category": "Power"},
                    {"description": "Power Supply Unit 5000W (Second Unit)", "sap": "SAP-PSU-5000-01", "category": "Power"},
                ]
            }
        ]
    },
    "Fuselage Integration Assembly": {
        "sub_assemblies": [
            {
                "name": "Fuselage Structure",
                "materials": [
                    {"description": "Carbon Fiber Fuselage Tube", "sap": "SAP-CF-FUSE-01", "category": "Composite"},
                    {"description": "Fuselage Access Panel Front", "sap": "SAP-ACCESS-FRONT-01", "category": "Composite"},
                    {"description": "Fuselage Access Panel Rear", "sap": "SAP-ACCESS-REAR-01", "category": "Composite"},
                ]
            },
            {
                "name": "Landing Gear",
                "materials": [
                    {"description": "Main Landing Gear Assembly", "sap": "SAP-GEAR-MAIN-01", "category": "Landing Gear"},
                    {"description": "Nose Landing Gear Assembly", "sap": "SAP-GEAR-NOSE-01", "category": "Landing Gear"},
                    {"description": "Shock Absorber Unit", "sap": "SAP-SHOCK-ABS-01", "category": "Landing Gear"},
                ]
            },
            {
                "name": "Avionics Bay",
                "materials": [
                    {"description": "Flight Control Computer", "sap": "SAP-FCC-01", "category": "Avionics"},
                    {"description": "Inertial Measurement Unit", "sap": "SAP-IMU-01", "category": "Avionics"},
                    {"description": "GPS Module", "sap": "SAP-GPS-01", "category": "Avionics"},
                    {"description": "Communication Module VHF", "sap": "SAP-COMM-VHF-01", "category": "Communication"},
                ]
            }
        ]
    },
    "Aircraft ERLM Assembly": {
        "sub_assemblies": [
            {
                "name": "Engine Assembly",
                "materials": [
                    {"description": "Main Turbo Engine 50cc", "sap": "SAP-ENGINE-50CC-01", "category": "Engine"},
                    {"description": "Engine Mount Assembly", "sap": "SAP-ENGINE-MOUNT-01", "category": "Hardware"},
                    {"description": "Engine Exhaust System", "sap": "SAP-EXHAUST-01", "category": "Engine"},
                ]
            },
            {
                "name": "Propulsion System",
                "materials": [
                    {"description": "Main Propeller Assembly", "sap": "SAP-MAIN-PROP-01", "category": "Propulsion"},
                    {"description": "Propeller Shaft Assembly", "sap": "SAP-PROP-SHAFT-01", "category": "Propulsion"},
                    {"description": "Gearbox Assembly", "sap": "SAP-GEARBOX-01", "category": "Transmission"},
                ]
            },
            {
                "name": "Flight Systems",
                "materials": [
                    {"description": "Hydraulic Pump Unit", "sap": "SAP-HYDRO-PUMP-01", "category": "Hydraulics"},
                    {"description": "Hydraulic Actuator Pack", "sap": "SAP-HYDRO-ACT-01", "category": "Hydraulics"},
                    {"description": "Flight Control Surface Linkage", "sap": "SAP-CTRL-LINK-01", "category": "Control Linkage"},
                ]
            }
        ]
    }
}

def seed_lm_kitting_materials():
    db = SessionLocal()
    
    try:
        # Check if kitting items already exist
        existing_items = db.query(KittingItem).count()
        if existing_items > 0:
            print(f"Kitting items already exist ({existing_items} items). Deleting and reseeding...")
            db.query(KittingItem).delete()
            db.commit()
        
        # Get all LM units
        lm_units = db.query(LoiteringMunition).all()
        if not lm_units:
            print("No LM units found. Please seed LM units first.")
            return
        
        total_items = 0
        
        # For each LM unit, add materials
        for lm_unit in lm_units:
            lm_serial = lm_unit.serial_number
            
            # For each route card
            for route_card_name, route_data in ROUTE_CARDS_MATERIALS.items():
                sub_assemblies = route_data.get("sub_assemblies", [])
                
                # For each sub-assembly
                for sub_assy in sub_assemblies:
                    sub_assy_name = sub_assy.get("name", "")
                    materials = sub_assy.get("materials", [])
                    
                    # For each material
                    for idx, material in enumerate(materials):
                        kitting_item = KittingItem()
                        kitting_item.product_serial_no = lm_serial
                        kitting_item.product_category = "LM"  # Fixed to be "LM" as expected by the route
                        kitting_item.route_card_description = f"{route_card_name} > {sub_assy_name}"  # Include sub-assembly
                        kitting_item.material_description = material.get("description", "")
                        kitting_item.sap_part_number = material.get("sap", "")
                        kitting_item.part_number = material.get("sap", "").replace("SAP-", "PN-")
                        
                        # Generate unique serial numbers for materials
                        # If same material is listed twice (like 2 batteries), they get different serials
                        material_serial_prefix = material.get("sap", "").split("-")[-1]
                        material_serial = f"{material_serial_prefix}-{lm_serial[-2:]}-{idx:03d}"
                        kitting_item.material_serial_no = material_serial
                        
                        kitting_item.batch_no_po_no = f"PO-{lm_serial}-{route_card_name[:3].upper()}-{idx}"
                        
                        db.add(kitting_item)
                        total_items += 1
        
        db.commit()
        total_units = len(lm_units)
        avg_per_unit = total_items // total_units if total_units > 0 else 0
        print(f"✅ Successfully created {total_items} kitting items")
        print(f"   - {total_units} LM units")
        print(f"   - {len(ROUTE_CARDS_MATERIALS)} route cards")
        print(f"   - ~{avg_per_unit} materials per LM unit")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding kitting materials: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    seed_lm_kitting_materials()
