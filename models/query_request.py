from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.sql import func

from database import Base


class QueryRequest(Base):
    __tablename__ = "query_requests"

    id = Column(Integer, primary_key=True, index=True)
    query_number = Column(String(50), unique=True, nullable=True)  # QRY-{Initials}-{Sequential}
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Open")
    priority = Column(String(50), nullable=False, default="Medium")
    query_type = Column(String(100), nullable=True)
    
    # Customer & Requestor
    caller = Column(String(200), nullable=True)  # Customer name
    requestor_name = Column(String(200), nullable=True)
    requestor_contact = Column(String(200), nullable=True)
    requestor_email = Column(String(200), nullable=True)
    customer_contract = Column(String(100), nullable=True)  # Kept for backward compatibility
    
    # Query Details
    subject = Column(String(300), nullable=True)
    assignment_group = Column(String(200), nullable=True)
    assigned_to = Column(String(200), nullable=True)
    
    # Notes & Audit
    notes = Column(Text, nullable=True)
    audit_log = Column(Text, nullable=True)  # JSON-formatted audit log of all changes
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<QueryRequest {self.id}: {self.title}>"
