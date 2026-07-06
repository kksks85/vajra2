"""
Seed script to create default users for the ALS - 50 Customer Service Management Portal.
Run this once to populate the database with sample users.
"""

import sys
# Set output encoding to UTF-8 to prevent console issues on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from database import SessionLocal
from models.admin import User
from services.auth import hash_password


def seed_users():
    """Create default users if they don't exist."""
    db = SessionLocal()
    
    default_users = [
        {
            "username": "admin",
            "email": "admin@vajra.com",
            "full_name": "Administrator",
            "password": "admin123",
            "role": "admin",
            "department": "Management",
            "location": "HQ",
            "employee_id": "EMP001",
            "status": "Active",
        },
        {
            "username": "technician",
            "email": "technician@vajra.com",
            "full_name": "John Technician",
            "password": "tech123",
            "role": "technician",
            "department": "Operations",
            "location": "Field Base 1",
            "employee_id": "EMP002",
            "status": "Active",
        },
        {
            "username": "supervisor",
            "email": "supervisor@vajra.com",
            "full_name": "Sarah Supervisor",
            "password": "super123",
            "role": "supervisor",
            "department": "Management",
            "location": "HQ",
            "employee_id": "EMP003",
            "status": "Active",
        },
        {
            "username": "agent",
            "email": "agent@vajra.com",
            "full_name": "Alex Agent",
            "password": "agent123",
            "role": "agent",
            "department": "Support",
            "location": "Support Center",
            "employee_id": "EMP004",
            "status": "Active",
        },
        {
            "username": "demo",
            "email": "demo@vajra.com",
            "full_name": "Demo User",
            "password": "demo123",
            "role": "agent",
            "department": "Demo",
            "location": "Demo Office",
            "employee_id": "EMP005",
            "status": "Active",
        },
    ]
    
    for user_data in default_users:
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.username == user_data["username"]
        ).first()
        
        if not existing_user:
            password = user_data.pop("password")
            user = User(
                **user_data,
                password_hash=hash_password(password),
                is_active=True,
            )
            db.add(user)
            print(f"[OK] Created user: {user_data['username']}")
        else:
            print(f"[OK] User already exists: {user_data['username']}")
    
    db.commit()
    db.close()
    print("\n[OK] User seeding completed!")


if __name__ == "__main__":
    seed_users()

