import sys
# Set output encoding to UTF-8 to prevent console issues on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from database import SessionLocal
from models.admin import User
from services.auth import verify_password

db = SessionLocal()

# Test the exact logic from the login endpoint
username = "admin"
password = "admin123"

print(f"Testing login for: {username}")

# Query database
user = db.query(User).filter(User.username == username, User.is_active == True).first()
print(f"User found: {user}")

if user:
    print(f"User email: {user.email}")
    print(f"User active: {user.is_active}")
    print(f"Password hash exists: {bool(user.password_hash)}")
    
    # Verify password
    is_valid = verify_password(password, user.password_hash)
    print(f"Password valid: {is_valid}")
    
    if is_valid:
        print("[OK] Login would succeed")
    else:
        print("[FAIL] Password mismatch")
else:
    print("[FAIL] User not found")

db.close()

