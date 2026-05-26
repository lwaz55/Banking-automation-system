from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.customer import Customer
from app.models.ticket import Ticket, InputEvent
from app.models.report import Report
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()


class CustomerProfile(BaseModel):
    id: str
    name: str
    segment: str
    loan_size: float
    risk_stage: int
    
    # CBS Fields
    dpd: int
    outstanding_balance: float
    payment_status: str
    ifrs9_stage: int
    history: str

    total_tickets: int
    open_tickets: int
    validated_reports: int
    ticket_history: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[Dict[str, Any]])
def list_customers(db: Session = Depends(get_db)):
    """
    Endpoint for list customers.
    """
    customers = db.query(Customer).order_by(Customer.id).all()
    result = []
    for c in customers:
        tickets = db.query(Ticket).filter(Ticket.customer_id == c.id).all()
        open_count = sum(1 for t in tickets if t.status == "open")
        result.append({
            "id": c.id,
            "name": c.name,
            "segment": c.segment,
            "loan_size": c.loan_size,
            "risk_stage": c.risk_stage,
            "total_tickets": len(tickets),
            "open_tickets": open_count,
        })
    return result


@router.get("/{customer_id}", response_model=CustomerProfile)
def get_customer_profile(customer_id: str, db: Session = Depends(get_db)):
    """
    Endpoint for get customer profile.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    tickets = db.query(Ticket).filter(Ticket.customer_id == customer_id).order_by(Ticket.id.desc()).all()

    open_tickets = sum(1 for t in tickets if t.status == "open")
    validated_reports = 0
    ticket_history = []

    for t in tickets:
        event = db.query(InputEvent).filter(InputEvent.ticket_id == t.id).first()
        reports = db.query(Report).filter(Report.ticket_id == t.id).all()
        validated = [r for r in reports if r.status in ("validated", "modified")]
        validated_reports += len(validated)

        ticket_history.append({
            "ticket_id": t.id,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "event_type": event.payload.get("event_type") if event else "unknown",
            "report_count": len(reports),
            "validated_count": len(validated),
        })

    return CustomerProfile(
        id=customer.id,
        name=customer.name,
        segment=customer.segment,
        loan_size=customer.loan_size,
        risk_stage=customer.risk_stage,
        dpd=customer.dpd,
        outstanding_balance=customer.outstanding_balance,
        payment_status=customer.payment_status,
        ifrs9_stage=customer.ifrs9_stage,
        history=customer.history,
        total_tickets=len(tickets),
        open_tickets=open_tickets,
        validated_reports=validated_reports,
        ticket_history=ticket_history,
    )
