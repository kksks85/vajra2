#!/usr/bin/env python3
"""Test script to check serial number update behavior"""

from database import SessionLocal
from models.entities import KittingItem

db = SessionLocal()

# Get a test item
item = db.query(KittingItem).filter(
    KittingItem.product_category == "LM",
    KittingItem.product_serial_no == "LM-SN-001-01"
).first()

if item:
    print(f"Original Item:")
    print(f"  ID: {item.id}")
    print(f"  Serial: {item.product_serial_no}")
    print(f"  Category: {item.product_category}")
    print(f"  Part Number: {item.part_number}")
    print(f"  SAP Part Number: {item.sap_part_number}")
    print(f"  Material Description: {item.material_description}")
    print(f"  Route Card: {item.route_card_description}")
    
    original_serial = item.product_serial_no
    original_part = item.part_number
    
    # Simulate updating the serial number
    item.product_serial_no = "LM-SN-004-01"
    item.part_number = "PN-UPDATED-TEST"
    
    print(f"\nAfter update (before commit):")
    print(f"  Serial: {item.product_serial_no}")
    print(f"  Part Number: {item.part_number}")
    
    # Check if it can still be queried by old serial
    old_query = db.query(KittingItem).filter(
        KittingItem.product_serial_no == original_serial,
        KittingItem.id == item.id
    ).first()
    print(f"\nQuery by old serial: {old_query is None}")
    
    # Check if it can be queried by new serial
    new_query = db.query(KittingItem).filter(
        KittingItem.product_serial_no == "LM-SN-004-01",
        KittingItem.id == item.id
    ).first()
    print(f"Query by new serial before commit: {new_query is not None}")
    
    # Rollback to avoid affecting database
    db.rollback()
    
    print(f"\nAfter rollback:")
    item_check = db.query(KittingItem).filter(KittingItem.id == item.id).first()
    if item_check:
        print(f"  Serial: {item_check.product_serial_no} (restored)")
        print(f"  Part Number: {item_check.part_number} (restored)")

else:
    print("No items found!")

db.close()
