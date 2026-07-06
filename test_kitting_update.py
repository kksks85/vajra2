#!/usr/bin/env python3
"""Test script to simulate updating a kitting item"""

from database import SessionLocal
from models.entities import KittingItem

db = SessionLocal()

# Get a test item
item = db.query(KittingItem).filter(
    KittingItem.product_category == "LM"
).order_by(KittingItem.id.desc()).first()

if item:
    print(f"Test Item Before Update:")
    print(f"ID: {item.id}")
    print(f"Product Serial: {item.product_serial_no}")
    print(f"Product Category: {item.product_category}")
    print(f"Route Card: {item.route_card_description}")
    print(f"Part Number: {item.part_number}")
    print(f"Data field: {item.data}")
    
    # Simulate update with empty product_category field
    print(f"\n--- Simulating Update (like form submission) ---")
    
    # Create form data as it would come from the form
    form_data = {
        'product_serial_no': item.product_serial_no,
        'route_card_description': item.route_card_description,
        'part_number': item.part_number,
        'material_description': item.material_description or '',
        'remarks': 'Updated by test script',
        # Note: product_category is NOT included (it's readonly in form)
    }
    
    print(f"Form data keys: {list(form_data.keys())}")
    print(f"product_category in form_data: {'product_category' in form_data}")
    
    # Check query that would match this item
    query = db.query(KittingItem).filter(
        KittingItem.id == item.id,
        KittingItem.product_category == "LM"
    )
    
    found_item = query.first()
    if found_item:
        print(f"\nItem would be found by update query: YES")
        print(f"Item ID: {found_item.id}")
    else:
        print(f"\nItem would be found by update query: NO (THIS IS THE PROBLEM!)")
    
    # Now check if product_category was changed
    print(f"\n--- Check if product_category would be changed ---")
    print(f"product_category input type: <input readonly ...>")
    print(f"Would readonly field be submitted? YES (readonly != disabled)")
    print(f"But product_category is not in form_data dict")
    print(f"So getattr(item, 'product_category', 'LM') would use old value: {item.product_category}")
    
else:
    print("No items found!")

db.close()
