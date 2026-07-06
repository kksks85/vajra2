from database import SessionLocal
from models.entities import LoiteringMunition

db = SessionLocal()
units = db.query(LoiteringMunition).limit(5).all()
for u in units:
    print(f'Unit: {u.unit_name}, Serial: {u.serial_number}')
    print(f'  Customer: {u.data.get("customer", "N/A")}')
    print(f'  Contract: {u.data.get("contract", "N/A")}')
    print(f'  Status: {u.data.get("status", "N/A")}')
    print()
db.close()
