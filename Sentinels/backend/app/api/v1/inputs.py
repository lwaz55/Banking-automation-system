from app.logger import logger
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.schemas.common import InputEventCreate
from app.security_layer.input_validator import validate_input_event
from app.security_layer.sanitizer import sanitize_payload
from app.security_layer.rate_limiter import check_rate_limit
from app.orchestrator.orchestrator import process_new_event
from app.models.ticket import Ticket, InputEvent
from app.core.audit import log_event
from app.api.v1.stream import broadcast_event_sync
from app.api.v1.auth import RequireRole
import threading

router = APIRouter()


def _run_pipeline(ticket_id: int, payload: dict):
    """
    Run the orchestrator pipeline in a background thread.
    Creates its own DB session so it doesn't share the request-scoped one.
    """
    db = SessionLocal()
    try:
        process_new_event(db, payload, ticket_id=ticket_id)
    except Exception as e:
        logger.info(f"[Orchestrator Error] Ticket {ticket_id}: {e}")
        import traceback; logger.error("Exception occurred", exc_info=True)
    finally:
        db.close()


@router.post("/", status_code=202, dependencies=[Depends(RequireRole(["OPERATOR", "ADMIN"]))])
def submit_input_event(event: InputEventCreate, request: Request, db: Session = Depends(get_db)):
    """
    Submit a new input event. Returns immediately with ticket_id so the
    frontend can redirect to the live ticket view while agents work.
    """
    # 1. Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    is_allowed, retry_after = check_rate_limit(client_ip)
    if not is_allowed:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Retry after {retry_after} seconds.")

    # 2. Input Sanitization
    sanitized_payload = sanitize_payload(event.payload)

    # 3. Validation (including Prompt Injection Detection)
    is_valid, error_msg = validate_input_event(sanitized_payload)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    payload = sanitized_payload
    customer_id = payload.get("customer_id")

    # Create ticket synchronously so we can return ticket_id immediately
    ticket = Ticket(customer_id=customer_id, status="open")
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    input_ev = InputEvent(ticket_id=ticket.id, source=event.source, payload=payload)
    db.add(input_ev)
    db.commit()

    log_event(db, "ticket_created", "ticket", ticket.id, details={
        "customer_id": customer_id,
        "event_type": payload.get("event_type"),
        "ticket_id": ticket.id,
    })

    broadcast_event_sync("ticket_created", {
        "ticket_id": ticket.id,
        "customer_id": customer_id,
        "event_type": payload.get("event_type"),
    })

    # Run agents in background thread
    t = threading.Thread(
        target=_run_pipeline,
        args=(ticket.id, payload),
        daemon=True,
    )
    t.start()

    return {
        "status": "accepted",
        "ticket_id": ticket.id,
        "message": "Event is being processed. Agents are activating.",
    }
