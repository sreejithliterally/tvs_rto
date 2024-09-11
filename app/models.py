from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import database
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Branch(database.Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    users = relationship("User", back_populates="branch")
    customers = relationship("Customer", back_populates="branch")

class User(database.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # "admin", "sales_executive", "accounts", "rto"
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True)  # Nullable for RTO/Admin who can access all branches
    is_active = Column(Boolean, default=True)

    branch = relationship("Branch", back_populates="users")

class Customer(database.Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone_number = Column(String, index=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    photo_adhaar = Column(String, nullable=True) 
    photo_passport = Column(String, nullable=True)  
    status = Column(String, default="pending")  
    token = Column(String, unique=True, index=True)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey('branches.id'))

    branch = relationship("Branch", back_populates="customers")

class VerificationLog(database.Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    action = Column(String)  # "sales_verified", "accounts_verified", "rto_approved"
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    customer = relationship("Customer")
