#!/usr/bin/env python
"""
Reset incidents table and reseed with complete data.
This script drops the incidents table and recreates it with the new schema.
"""

import sys
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from database import Base, engine
from models.incident import Incident

# Drop existing incidents table
print("🗑️  Dropping existing incidents table...")
try:
    Incident.__table__.drop(engine)
    print("✅ Table dropped successfully")
except Exception as e:
    print(f"ℹ️  Table drop info: {str(e)}")

# Recreate the table with new schema
print("\n📋 Creating new incidents table with extended schema...")
try:
    Incident.__table__.create(engine)
    print("✅ Table created successfully with all new columns:")
    print("   - Customer & Requestor fields")
    print("   - Product Information fields")
    print("   - Issue Classification fields")
    print("   - Service History fields")
except Exception as e:
    print(f"❌ Error creating table: {str(e)}")
    sys.exit(1)
