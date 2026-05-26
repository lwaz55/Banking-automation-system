from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    department_id = Column(String, ForeignKey("departments.id"))
    content = Column(JSON)
    status = Column(String, default="pending") # pending, validated, invalidated

    ticket = relationship("Ticket", back_populates="reports")
    department = relationship("Department")
