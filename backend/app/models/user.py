from sqlalchemy import Column,Integer,String
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__="users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    auth_provider = Column(String(50), default="local")
    jobs = relationship("Job", back_populates="owner")