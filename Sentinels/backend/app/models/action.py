from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    department_id = Column(String, ForeignKey("departments.id"))
    action_taken = Column(String)
    status = Column(String, default="executed")
    timestamp = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report")
    department = relationship("Department")
