"""
All ORM models for EEF (Section 30). Kept in one module to guarantee a single
metadata registration order and avoid circular imports; each domain also gets
a thin re-export file (app/models/user.py etc.) matching the requested
project layout, per data model conventions used across the platform.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# ---------------------------------------------------------------- Enums ----
class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class DocumentType(str, enum.Enum):
    NATIONAL_ID = "NATIONAL_ID"
    PASSPORT = "PASSPORT"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    EMPLOYEE_ID = "EMPLOYEE_ID"
    RESIDENCE_PERMIT = "RESIDENCE_PERMIT"


class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class AlertType(str, enum.Enum):
    DEEPFAKE_DETECTED = "DEEPFAKE_DETECTED"
    FAKE_DOCUMENT = "FAKE_DOCUMENT"
    VOICE_CLONE_SUSPECTED = "VOICE_CLONE_SUSPECTED"
    IDENTITY_THEFT = "IDENTITY_THEFT"
    DEVICE_ANOMALY = "DEVICE_ANOMALY"
    MULTIPLE_IDENTITY_USAGE = "MULTIPLE_IDENTITY_USAGE"
    LOW_LIVENESS = "LOW_LIVENESS"
    FACE_MISMATCH = "FACE_MISMATCH"
    HIGH_RISK_IDENTITY = "HIGH_RISK_IDENTITY"


class ModelType(str, enum.Enum):
    REAL_MODEL = "REAL_MODEL"
    HEURISTIC = "HEURISTIC"
    DEMO_SIMULATION = "DEMO_SIMULATION"


class FraudCaseStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CLOSED = "CLOSED"


# ---------------------------------------------------------------- Models ----
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    full_name = Column(String(128))
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(16), default=Role.VIEWER.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    identity = relationship("Identity", back_populates="user", uselist=False)


class Identity(Base):
    """A subject/customer identity profile (distinct from the platform's login Users)."""
    __tablename__ = "identities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    full_name = Column(String(128), nullable=False, index=True)
    email = Column(String(128), index=True)
    phone = Column(String(32), index=True)
    date_of_birth = Column(String(32))
    nationality = Column(String(64))
    external_ref = Column(String(64), index=True)  # e.g. customer ID
    trust_score_cached = Column(Float, default=0.0)
    risk_level_cached = Column(String(16), default=RiskLevel.MEDIUM.value)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="identity")
    documents = relationship("Document", back_populates="identity")
    verifications = relationship("VerificationSession", back_populates="identity")
    devices = relationship("DeviceLink", back_populates="identity")
    ip_links = relationship("IPLink", back_populates="identity")


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    device_fingerprint = Column(String(128), unique=True, nullable=False, index=True)
    device_type = Column(String(32))
    os = Column(String(64))
    first_seen = Column(DateTime, default=datetime.utcnow)

    links = relationship("DeviceLink", back_populates="device")


class DeviceLink(Base):
    __tablename__ = "device_links"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    linked_at = Column(DateTime, default=datetime.utcnow)

    identity = relationship("Identity", back_populates="devices")
    device = relationship("Device", back_populates="links")


class IPAddress(Base):
    __tablename__ = "ip_addresses"
    id = Column(Integer, primary_key=True)
    ip = Column(String(64), unique=True, nullable=False, index=True)
    country = Column(String(64))
    is_high_risk = Column(Boolean, default=False)
    first_seen = Column(DateTime, default=datetime.utcnow)

    links = relationship("IPLink", back_populates="ip")


class IPLink(Base):
    __tablename__ = "ip_links"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    ip_id = Column(Integer, ForeignKey("ip_addresses.id"), nullable=False)
    linked_at = Column(DateTime, default=datetime.utcnow)

    identity = relationship("Identity", back_populates="ip_links")
    ip = relationship("IPAddress", back_populates="links")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    document_type = Column(String(32), nullable=False)
    document_number = Column(String(64), index=True)
    file_path = Column(String(255))
    file_hash = Column(String(128), index=True)  # for duplicate detection
    ocr_text = Column(Text)
    extracted_fields = Column(JSON, default=dict)
    ocr_confidence = Column(Float, default=0.0)
    document_score = Column(Float, default=0.0)
    anomalies = Column(JSON, default=list)
    model_type = Column(String(24), default=ModelType.HEURISTIC.value)
    created_at = Column(DateTime, default=datetime.utcnow)

    identity = relationship("Identity", back_populates="documents")


class VerificationSession(Base):
    __tablename__ = "verification_sessions"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    status = Column(String(24), default=VerificationStatus.PROCESSING.value)
    identity_match_score = Column(Float, default=0.0)
    liveness_score = Column(Float, default=0.0)
    document_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0)
    fraud_indicators = Column(JSON, default=list)
    explanation = Column(JSON, default=dict)
    device_fingerprint = Column(String(128))
    ip_address = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)

    identity = relationship("Identity", back_populates="verifications")
    face_result = relationship("FaceResult", back_populates="verification", uselist=False)
    liveness_result = relationship("LivenessResult", back_populates="verification", uselist=False)


class FaceResult(Base):
    __tablename__ = "face_results"
    id = Column(Integer, primary_key=True)
    verification_id = Column(Integer, ForeignKey("verification_sessions.id"), nullable=True)
    similarity_score = Column(Float, default=0.0)
    match_decision = Column(Boolean, default=False)
    faces_detected_reference = Column(Integer, default=0)
    faces_detected_comparison = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    threshold_used = Column(Float, default=0.0)
    model_type = Column(String(24), default=ModelType.HEURISTIC.value)
    created_at = Column(DateTime, default=datetime.utcnow)

    verification = relationship("VerificationSession", back_populates="face_result")


class LivenessResult(Base):
    __tablename__ = "liveness_results"
    id = Column(Integer, primary_key=True)
    verification_id = Column(Integer, ForeignKey("verification_sessions.id"), nullable=True)
    liveness_score = Column(Float, default=0.0)
    challenge = Column(JSON, default=list)
    completed_steps = Column(JSON, default=list)
    spoof_indicators = Column(JSON, default=list)
    mode = Column(String(16), default="PASSIVE")  # ACTIVE | PASSIVE
    model_type = Column(String(24), default=ModelType.HEURISTIC.value)
    created_at = Column(DateTime, default=datetime.utcnow)

    verification = relationship("VerificationSession", back_populates="liveness_result")


class DeepfakeResult(Base):
    __tablename__ = "deepfake_results"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=True)
    media_type = Column(String(16))  # IMAGE | VIDEO
    file_path = Column(String(255))
    deepfake_probability = Column(Float, default=0.0)
    real_probability = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    indicators = Column(JSON, default=list)
    frame_results = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)
    model_type = Column(String(24), default=ModelType.HEURISTIC.value)
    created_at = Column(DateTime, default=datetime.utcnow)


class VoiceResult(Base):
    __tablename__ = "voice_results"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=True)
    file_path = Column(String(255))
    duration_seconds = Column(Float, default=0.0)
    sample_rate = Column(Integer, default=0)
    transcript = Column(Text)
    speaker_score = Column(Float, default=0.0)
    audio_quality = Column(Float, default=0.0)
    risk_indicators = Column(JSON, default=list)
    decision = Column(String(24), default="REVIEW_REQUIRED")
    model_type = Column(String(24), default=ModelType.HEURISTIC.value)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrustScore(Base):
    __tablename__ = "trust_scores"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    verification_id = Column(Integer, ForeignKey("verification_sessions.id"), nullable=True)
    trust_score = Column(Float, default=0.0)
    risk_level = Column(String(16), default=RiskLevel.MEDIUM.value)
    positive_signals = Column(JSON, default=list)
    negative_signals = Column(JSON, default=list)
    weights_used = Column(JSON, default=dict)
    explanation = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class FraudCase(Base):
    __tablename__ = "fraud_cases"
    id = Column(Integer, primary_key=True)
    severity = Column(String(16), default=RiskLevel.MEDIUM.value)
    status = Column(String(16), default=FraudCaseStatus.OPEN.value)
    signals = Column(JSON, default=list)
    related_identities = Column(JSON, default=list)  # list of identity IDs
    related_devices = Column(JSON, default=list)
    related_documents = Column(JSON, default=list)
    investigation_notes = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    type = Column(String(32), nullable=False)
    severity = Column(String(16), default=RiskLevel.MEDIUM.value)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=True)
    description = Column(Text)
    evidence = Column(JSON, default=dict)
    status = Column(String(16), default=AlertStatus.OPEN.value)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor = Column(String(64))
    action = Column(String(64), nullable=False, index=True)
    resource = Column(String(128))
    result = Column(String(24))
    ip = Column(String(64))
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
