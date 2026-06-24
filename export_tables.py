import sqlite3
import csv
import os
import sys

# Add the root directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from routers.admin import (
        _get_sample_customers,
        _get_sample_contracts,
        _get_sample_lrus,
        _get_sample_units,
    )
except ImportError:
    _get_sample_customers = None

def export_db_tables():
    """Export SQLite tables to CSV."""
    db_file = "vajra.db"
    if not os.path.exists(db_file):
        print(f"❌ Database file {db_file} not found. Please run init_db.py and run the app first.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith("sqlite_")]
    
    os.makedirs("exported_tables", exist_ok=True)
    
    print("--- SQLite Database Tables ---")
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        csv_file = f"exported_tables/{table}.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
        print(f"[OK] Exported SQLite table '{table}' ({len(rows)} rows) to: {csv_file}")
    
    conn.close()

def export_mock_tables():
    """Export hardcoded mock tables (Customers, Contracts, LRUs, Units) to CSV."""
    if not _get_sample_customers:
        print("❌ Could not import sample data from routers/admin.py")
        return

    os.makedirs("exported_tables", exist_ok=True)
    print("\n--- In-Memory Application Tables ---")
    
    # Export Customers
    customers = _get_sample_customers()
    if customers:
        keys = customers[0].keys()
        csv_file = "exported_tables/customers_list.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(customers)
        print(f"[OK] Exported mock table 'customers' ({len(customers)} rows) to: {csv_file}")

    # Export Contracts
    contracts = _get_sample_contracts()
    if contracts:
        keys = contracts[0].keys()
        csv_file = "exported_tables/contracts_list.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(contracts)
        print(f"[OK] Exported mock table 'contracts' ({len(contracts)} rows) to: {csv_file}")

    # Export Units (LM, GCS, TMV, SIM)
    for unit_type in ["LM", "GCS", "TMV", "SIM"]:
        units = _get_sample_units(unit_type)
        if units:
            keys = units[0].keys()
            csv_file = f"exported_tables/units_{unit_type.lower()}.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(units)
            print(f"[OK] Exported mock table 'units_{unit_type.lower()}' ({len(units)} rows) to: {csv_file}")

    # Export LRUs
    lrus = _get_sample_lrus()
    if lrus:
        keys = lrus[0].keys()
        csv_file = "exported_tables/lrus.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(lrus)
        print(f"[OK] Exported mock table 'lrus' ({len(lrus)} rows) to: {csv_file}")

if __name__ == "__main__":
    export_db_tables()
    export_mock_tables()
    print(f"\n[DONE] All tables successfully exported into the 'exported_tables' directory!")
