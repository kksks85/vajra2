from database import SessionLocal
from models.entities import Contract
import json

db = SessionLocal()
contracts = db.query(Contract).all()
print(f'Total contracts: {len(contracts)}')
for c in contracts[:3]:
    print(f'\nContract {c.id}: {c.number}')
    print(f'Data keys: {list(c.data.keys())}')
    print(f'Full data: {json.dumps(c.data, indent=2)}')
db.close()
