from sqlalchemy import Boolean, Column, DateTime, Integer, String, JSON
from sqlalchemy.sql import func

from database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), default="")
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), default="")
    max_users = Column(Integer, nullable=False)
    features = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False, default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="agent")
    license_type = Column(String(50), default="Standard")
    department = Column(String(100), default="")
    location = Column(String(100), default="")
    employee_id = Column(String(50), unique=True, nullable=True)
    specialization = Column(String(200), default="")
    phone = Column(String(20), default="")
    hire_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="Active")
    is_active = Column(Boolean, default=True, nullable=False)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), default="")
    user_ids = Column(JSON, default=list)
    member_count = Column(Integer, default=0)
    data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
