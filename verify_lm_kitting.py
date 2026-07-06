from database import SessionLocal
from models.entities import LoiteringMunition, KittingItem
from sqlalchemy import func

db = SessionLocal()

try:
    # Get all LM units
    lm_units = db.query(LoiteringMunition).order_by(LoiteringMunition.id).all()
    print(f"Total LM units: {len(lm_units)}\n")
    
    # Check distribution for each LM
    for lm in lm_units:
        lm_serial = lm.serial_number
        lm_name = lm.unit_name
        
        # Count kitting items per LM
        total_items = db.query(KittingItem).filter(KittingItem.product_serial_no == lm_serial).count()
        
        # Count unique route cards
        route_cards = db.query(KittingItem.route_card_description).filter(
            KittingItem.product_serial_no == lm_serial
        ).distinct().all()
        
        route_card_list = [rc[0] for rc in route_cards]
        
        print(f"{lm_name} ({lm_serial})")
        print(f"  Total items: {total_items}")
        print(f"  Route cards: {len(route_card_list)}")
        if len(route_card_list) < 9:
            print(f"  ❌ MISSING route cards!")
            all_route_cards = [
                "LH Side Wing Integration Assembly",
                "RH Side Wing Integration Assembly",
                "LH Empennage Integration Assembly",
                "RH Empennage Integration Assembly",
                "VTOL Boom Bracket Integration Assembly LH",
                "VTOL Boom Bracket Integration Assembly RH",
                "Centre Wing Integration Assembly",
                "Fuselage Integration Assembly",
                "Aircraft ERLM Assembly"
            ]
            missing = [rc for rc in all_route_cards if rc not in route_card_list]
            for m in missing:
                print(f"    - {m}")
        print()
        
finally:
    db.close()
