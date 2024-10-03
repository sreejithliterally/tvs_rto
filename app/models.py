from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, DECIMAL, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import database
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Branch(database.Base):
    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    branch_manager = Column(String, nullable=False)


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
    chassis_data = relationship("Chassis", back_populates="user")

class Customer(database.Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    alternate_phone_number = Column(String)
    dob = Column(Date, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    photo_adhaar_front = Column(String, nullable=True)
    photo_adhaar_back = Column(String, nullable=True)
    photo_passport = Column(String, nullable=True)

    nominee = Column(String)
    relation = Column(String)
    vehicle_name = Column(String)   
    vehicle_variant = Column(String)
    vehicle_color = Column(String)
    ex_showroom_price = Column(DECIMAL(10, 2))
    tax = Column(DECIMAL(10, 2))
    insurance = Column(DECIMAL(10, 2))
    tp_registration = Column(DECIMAL(10, 2))
    man_accessories = Column(DECIMAL(10, 2))
    optional_accessories = Column(DECIMAL(10, 2))
    total_price = Column(DECIMAL(10, 2))
    finance_amount = Column(DECIMAL(10, 2),nullable=True)
    booking = Column(DECIMAL(10,2),nullable=True)

    link_token = Column(String, unique=True, index=True)  # Unique token for the link
    link_expiration = Column(Boolean, default=False)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey('branches.branch_id'))
    sales_executive_id = Column(Integer, ForeignKey('users.user_id'))
    finance_id = Column(Integer, ForeignKey('finance_options.finance_id'), nullable=True)

    sales_verified = Column(Boolean, default=False)
    accounts_verified = Column(Boolean, default=False)
    rto_verified = Column(Boolean, default=False)

    
    

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


class Chassis(database.Base):
    __tablename__ = "chassis"

    id = Column(Integer, primary_key=True, index=True)
    chassis_number = Column(String, unique=True, nullable=False)
    chassis_photo_url = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="chassis_data")
