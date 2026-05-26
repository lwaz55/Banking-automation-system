from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    segment = Column(String)
    loan_size = Column(Float)
    risk_stage = Column(Integer)
    
    # Simulated Core Banking System (CBS) fields
    dpd = Column(Integer, default=0)
    outstanding_balance = Column(Float, default=0.0)
    payment_status = Column(String, default="current")  # current, late, default
    ifrs9_stage = Column(Integer, default=1)
    history = Column(String, default="")
