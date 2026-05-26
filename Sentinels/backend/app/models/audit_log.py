from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)  # ticket_created, agent_started, agent_done, report_validated, report_invalidated, report_modified, action_executed
    entity_type = Column(String)             # ticket, report, action
    entity_id = Column(String)
    actor = Column(String, default="system") # system or username
    details = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    signature = Column(String)               # SHA-256 chained hash
