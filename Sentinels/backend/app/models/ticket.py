from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"))
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer")
    reports = relationship("Report", back_populates="ticket")

class InputEvent(Base):
    __tablename__ = "input_events"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    source = Column(String)
    payload = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
