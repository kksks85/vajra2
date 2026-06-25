from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(100), unique=True, nullable=False)
    customer_id = Column(Integer, nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BatteryType(Base):
    __tablename__ = "battery_types"

    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(200), nullable=False)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Battery(Base):
    __tablename__ = "batteries"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    serial_number = Column(String(120), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Warhead(Base):
    __tablename__ = "warheads"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LoiteringMunition(Base):
    __tablename__ = "loitering_munitions"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    serial_number = Column(String(120), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GroundControlSystem(Base):
    __tablename__ = "ground_control_systems"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    serial_number = Column(String(120), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TacticalMobilityVehicle(Base):
    __tablename__ = "tactical_mobility_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    serial_number = Column(String(120), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SimulatorUnit(Base):
    __tablename__ = "simulators"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    serial_number = Column(String(120), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RapidDeploymentVehicle(Base):
    __tablename__ = "rapid_deployment_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    serial_number = Column(String(120), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MRLS(Base):
    __tablename__ = "mrls"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LineReplaceableUnit(Base):
    __tablename__ = "lrus"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SMTSTE(Base):
    __tablename__ = "smt_stes"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SAM(Base):
    __tablename__ = "sams"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SubSystem(Base):
    __tablename__ = "sub_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
