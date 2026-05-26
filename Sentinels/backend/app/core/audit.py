import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session


def log_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: str,
    actor: str = "system",
    details: dict = None,
):
    """
    Append a chained audit log entry.
    Each entry's signature is SHA-256(prev_signature | event_type | entity | actor | details).
    This creates an immutable, tamper-evident chain — if any entry is altered, all subsequent
    signatures become invalid.
    """
    from app.models.audit_log import AuditLog

    # Get previous entry for chain
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_signature = last_log.signature if last_log else "genesis_block_sentinels_stb"

    details_str = json.dumps(details or {}, sort_keys=True, ensure_ascii=False)
    payload = f"{prev_signature}|{event_type}|{entity_type}|{entity_id}|{actor}|{details_str}"
    signature = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    log = AuditLog(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor=actor,
        details=details or {},
        created_at=datetime.utcnow(),
        signature=signature,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
