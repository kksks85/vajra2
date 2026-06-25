from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from database import Base


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(String(50), nullable=False)  # manual, service_bulletin, operator_bulletin, amendments_leaflet, incoming_letter, outgoing_letter
    file_reference_number = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    date_of_issue = Column(String(50), nullable=False)  # YYYY-MM-DD
    subject_line = Column(String(300), nullable=False)
    description = Column(Text, default="Please refer to the attached document")
    attachments = Column(JSON, default=list)  # List of filenames
    data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
