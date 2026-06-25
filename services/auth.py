from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.admin import User

# Use pbkdf2_sha256 - pure Python, no C extensions needed
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_user(
    db: Session,
    *,
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str = "admin",
    data: dict | None = None,
) -> User:
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        data=data or {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
