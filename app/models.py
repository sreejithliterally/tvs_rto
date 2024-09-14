from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
import database
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Branch(database.Base):
    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    users = relationship("User", back_populates="branch")
    customers = relationship("Customer", back_populates="branch")

class Role(database.Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True)


class User(database.Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    branch_id = Column(Integer, ForeignKey('branches.branch_id'), nullable=True)  # Nullable for RTO/Admin who can access all branches
    is_active = Column(Boolean, default=True)

    branch = relationship("Branch", back_populates="users")


class Customer(database.Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    photo_adhaar_front = Column(String, nullable=True)
    photo_adhaar_back = Column(String, nullable=True)
    photo_passport = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.branch_id'))
    sales_executive_id = Column(Integer, ForeignKey('users.user_id'))
    vehicle_name = Column(String)
    vehicle_variant = Column(String)
    ex_showroom_price = Column(DECIMAL(10, 2))
    tax = Column(DECIMAL(10, 2))
    onroad_price = Column(DECIMAL(10, 2))
    finance_id = Column(Integer, ForeignKey('finance_options.finance_id'), nullable=True)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", back_populates="customers")


class VerificationLog(database.Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    action = Column(String)  # "sales_verified", "accounts_verified", "rto_approved"
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    customer = relationship("Customer")


class FinanceOption(database.Base):
    __tablename__ = "finance_options"

    finance_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True)
    details = Column(String)




class Transaction(database.Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    finance_id = Column(Integer, ForeignKey('finance_options.finance_id'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.branch_id'))
    sales_executive_id = Column(Integer, ForeignKey('users.user_id'))
    total_price = Column(DECIMAL(10, 2))
    payment_status = Column(String, default='Pending')
    payment_verified = Column(Boolean, default=False)
    finance_verified = Column(Boolean, default=False)
    rto_submitted = Column(Boolean, default=False)
    transaction_date = Column(DateTime, default=datetime.utcnow)
