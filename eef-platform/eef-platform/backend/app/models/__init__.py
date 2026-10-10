"""Import every ORM model so SQLAlchemy's Base.metadata sees all tables."""
from app.models._all import (  # noqa: F401
    Role, DocumentType, VerificationStatus, RiskLevel, AlertStatus, AlertType,
    ModelType, FraudCaseStatus,
    User, Identity, Device, DeviceLink, IPAddress, IPLink, Document,
    VerificationSession, FaceResult, LivenessResult, DeepfakeResult,
    VoiceResult, TrustScore, FraudCase, Alert, AuditLog,
)
