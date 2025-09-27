from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .db_config import Base

class PatientReport(Base):
    __tablename__ = "patient_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_email = Column(String, index=True, nullable=False)
    mpin = Column(String, nullable=False)  # Medical PIN for patient authentication
    report_type = Column(String, nullable=False)
    report_content = Column(Text, nullable=False)
    test_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PublishedReport(Base):
    __tablename__ = "published_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    original_report_id = Column(UUID(as_uuid=True), ForeignKey("patient_reports.id"), nullable=False)
    anonymized_content = Column(Text, nullable=False)
    report_type = Column(String, nullable=False)
    test_date = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # For marketplace features
    title = Column(String, nullable=False)
    description = Column(Text)
    tags = Column(String)  # JSON string of tags
    is_active = Column(Boolean, default=True)
    
    # For buyer agent - pricing and payment
    price_eth = Column(Float, nullable=False, default=0.001)  # Price in ETH
    seller_wallet = Column(Text, nullable=False)  # Wallet address to receive payment