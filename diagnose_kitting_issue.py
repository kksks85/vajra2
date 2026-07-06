#!/usr/bin/env python3
"""Diagnostic script to check kitting item deletion issue"""

from database import SessionLocal
from models.entities import KittingItem

db = SessionLocal()

# Get total count of LM kitting items
total_count = db.query(KittingItem).filter(KittingItem.product_category == "LM").count()
print(f"Total LM Kitting Items in database: {total_count}")

# Get items by serial number
print("\n--- Items by Product Serial Number ---")
serials = db.query(KittingItem.product_serial_no).filter(
    KittingItem.product_category == "LM"
).distinct().all()

for (serial,) in serials:
    count = db.query(KittingItem).filter(
        KittingItem.product_category == "LM",
        KittingItem.product_serial_no == serial
    ).count()
    print(f"{serial}: {count} items")

# Check for NULL product_category
null_category = db.query(KittingItem).filter(
    KittingItem.product_category.is_(None)
).count()
print(f"\n--- Data Quality Check ---")
print(f"Items with NULL product_category: {null_category}")

# Check for empty product_serial_no
empty_serial = db.query(KittingItem).filter(
    KittingItem.product_serial_no == "" or KittingItem.product_serial_no.is_(None)
).count()
print(f"Items with empty product_serial_no: {empty_serial}")

# Check recent items
print("\n--- 5 Most Recent Items (by ID DESC) ---")
recent = db.query(KittingItem).filter(
    KittingItem.product_category == "LM"
).order_by(KittingItem.id.desc()).limit(5).all()

for item in recent:
    print(f"ID: {item.id} | Serial: {item.product_serial_no} | Route: {item.route_card_description} | Part: {item.part_number}")
    print(f"  Data field: {item.data}")

db.close()
