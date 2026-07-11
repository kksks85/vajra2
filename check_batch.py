from database import SessionLocal
from models.incident import Incident
import json

db = SessionLocal()
incident = db.query(Incident).filter(Incident.id == 8).first()

print('Last 2 entries in audit log:')
entries = [l for l in incident.audit_log.strip().split('\n') if l.strip()]
print(f'Total entries: {len(entries)}\n')

for i, entry_data in enumerate(entries[-2:], 1):
    entry = json.loads(entry_data)
    print(f'Entry {len(entries) - 2 + i}:')
    print(f'  Time: {entry.get("date_time")}')
    has_changes_dict = "changes" in entry
    print(f'  Format: {"changes dict" if has_changes_dict else "old format"}')
    if has_changes_dict:
        print(f'  Changes: {list(entry["changes"].keys())}')
    elif 'field' in entry:
        print(f'  Field: {entry["field"]}')
    print(f'  Work note: {entry.get("work_note", "")}')
    print()
