from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)

    users = relationship("User", back_populates="department")
