from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.ticket import Ticket, InputEvent
from app.models.report import Report
from app.schemas.common import TicketOut
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any, Dict

router = APIRouter()


class TicketDetailOut(BaseModel):
    id: int
    customer_id: str
    status: str
    created_at: datetime
    input_payload: Optional[Dict[str, Any]] = None
    report_count: int = 0
    validated_count: int = 0

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[TicketDetailOut])
def list_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Endpoint for list tickets.
    """
    tickets = db.query(Ticket).order_by(Ticket.id.desc()).offset(skip).limit(limit).all()
    result = []
    for t in tickets:
        # Get input event payload
        event = db.query(InputEvent).filter(InputEvent.ticket_id == t.id).first()
        reports = db.query(Report).filter(Report.ticket_id == t.id).all()
        validated = [r for r in reports if r.status in ("validated", "modified")]
        result.append(TicketDetailOut(
            id=t.id,
            customer_id=t.customer_id,
            status=t.status,
            created_at=t.created_at,
            input_payload=event.payload if event else None,
            report_count=len(reports),
            validated_count=len(validated),
        ))
    return result


@router.get("/{ticket_id}", response_model=TicketDetailOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Endpoint for get ticket.
    """
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    event = db.query(InputEvent).filter(InputEvent.ticket_id == t.id).first()
    reports = db.query(Report).filter(Report.ticket_id == t.id).all()
    validated = [r for r in reports if r.status in ("validated", "modified")]
    return TicketDetailOut(
        id=t.id,
        customer_id=t.customer_id,
        status=t.status,
        created_at=t.created_at,
        input_payload=event.payload if event else None,
        report_count=len(reports),
        validated_count=len(validated),
    )
