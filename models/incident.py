from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="new")
    priority = Column(String(50), nullable=False, default="medium")
    issue_type = Column(String(100), nullable=True)
    stage = Column(String(50), nullable=False, default="triage")
    
    # Customer & Requestor
    caller = Column(String(200), nullable=True)  # Customer name
    requestor_name = Column(String(200), nullable=True)
    customer_contract = Column(String(100), nullable=True)
    requestor_contact = Column(String(200), nullable=True)
    
    # Product Information
    srlm_system = Column(String(100), nullable=True)  # SRLM/ERLM
    platform_variant = Column(String(200), nullable=True)  # Product category (LM, GCS, TMV, etc.)
    line_replaceable_unit = Column(String(100), nullable=True)  # Serial number
    sub_system = Column(String(200), nullable=True)
    
    # Issue Classification
    assignment_group = Column(String(200), nullable=True)
    assigned_to = Column(String(200), nullable=True)
    sla = Column(String(100), nullable=True)
    
    # Service History
    warranty_status = Column(String(50), nullable=True)
    last_serviced_date = Column(String(50), nullable=True)
    
    # Repair Execution Fields
    repair_execution = Column(String(100), nullable=True)  # e.g., "Standard Repair"
    repair_status = Column(String(200), nullable=True)  # e.g., "1. Initial Inspection"
    
    # Repair Execution Status (stores status name directly)
    repair_execution_status = Column(String(200), nullable=True)
    
    # Notes & Audit
    work_notes = Column(Text, nullable=True)  # Work notes by technicians
    audit_log = Column(Text, nullable=True)  # JSON-formatted audit log of all changes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
