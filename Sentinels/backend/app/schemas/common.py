from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime

class DepartmentBase(BaseModel):
    id: str
    name: str
    type: str

class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    username: str
    role: str
    department_id: str

class UserOut(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CustomerBase(BaseModel):
    id: str
    name: str
    segment: str
    loan_size: float
    risk_stage: int

class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

class TicketBase(BaseModel):
    customer_id: str
    status: str = "open"

class TicketOut(TicketBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReportBase(BaseModel):
    ticket_id: int
    department_id: str
    content: Dict[str, Any]
    status: str = "pending"

class ReportOut(ReportBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ActionBase(BaseModel):
    report_id: int
    department_id: str
    action_taken: str
    status: str = "executed"

class ActionOut(ActionBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class InputEventCreate(BaseModel):
    source: str
    payload: Dict[str, Any]

class InputEventOut(InputEventCreate):
    id: int
    ticket_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
