from database import SessionLocal
from models.admin import User
from services.auth import hash_password, verify_password

db = SessionLocal()

# Get the admin user
admin_user = db.query(User).filter(User.username == 'admin').first()
print(f'Admin user found: {admin_user}')
print(f'Admin password hash: {admin_user.password_hash[:50]}...')

# Test password verification
test_password = 'admin123'
result = verify_password(test_password, admin_user.password_hash)
print(f'Password verification result: {result}')

# Also test hashing a fresh password
fresh_hash = hash_password(test_password)
print(f'Fresh hash: {fresh_hash[:50]}...')

# Test if fresh hash verifies
fresh_result = verify_password(test_password, fresh_hash)
print(f'Fresh hash verification: {fresh_result}')

db.close()
