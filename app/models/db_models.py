from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class DBUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Integer, default=1)
    role = Column(String, default="reviewer")

class DBAuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String)
    user = Column(String) # user (mock or real)
    changes = Column(JSON, nullable=True)
    document_id = Column(String, index=True, nullable=True)

class DBDocument(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String)
    content_type = Column(String)
    size = Column(Integer)
    file_type = Column(String)
    pages = Column(Integer)
    quality_score = Column(Float)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="uploaded")
    doc_type = Column(String, default="bidder")
    parent_tender_id = Column(String, ForeignKey("documents.id"), nullable=True)
    final_verdict = Column(String, nullable=True)
    expert_reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)

    reviewer = relationship("DBUser")

class DBHITLReview(Base):
    __tablename__ = "hitl_reviews"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(ForeignKey("documents.id"))
    reviewer_id = Column(ForeignKey("users.id"))
    decision = Column(String)
    reason = Column(Text)
    corrections = Column(JSON)
    original_evaluation = Column(JSON)
    final_overall_score = Column(Float)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)

    document = relationship("DBDocument")
    reviewer = relationship("DBUser")

class DBTenderCriterion(Base):
    __tablename__ = "tender_criteria"

    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, ForeignKey("documents.id"), index=True)
    type = Column(String)
    description = Column(Text)
    threshold = Column(String, nullable=True)
    comparator = Column(String, nullable=True)
