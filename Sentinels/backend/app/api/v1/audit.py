from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.audit_log import AuditLog
from app.api.v1.auth import RequireRole
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()

class AuditLogOut(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: str
    actor: str
    details: dict
    created_at: datetime
    signature: str

    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[AuditLogOut], dependencies=[Depends(RequireRole(["ADMIN"]))])
def get_audit_log(
    ticket_id: Optional[str] = None,
    dept_id: Optional[str] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """Return the full chained audit log, optionally filtered."""
    query = db.query(AuditLog).order_by(AuditLog.id.desc())
    logs = query.limit(limit).all()

    # Apply lightweight filters on details JSON (SQLite doesn't support JSON path)
    if ticket_id:
        logs = [l for l in logs if str(l.details.get("ticket_id", "")) == str(ticket_id)]
    if dept_id:
        logs = [l for l in logs if l.details.get("dept_id") == dept_id]

    return logs
