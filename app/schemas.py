from datetime import datetime, date
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role_id: int
    branch_id: Optional[int] = None

class UserOut(BaseModel):
    user_id: int
    first_name: str
    last_name: Optional[str]  # Assuming last_name is optional
    email: str
    branch_id: Optional[int]
    role_name: str

class CustomerBase(BaseModel):
    name: str
    phone_number: str
    alternate_phone_number : str
    vehicle_name: str
    vehicle_variant: str
    vehicle_color: Optional[str] = None
    ex_showroom_price: float
    tax: float
    insurance: float
    tp_registration : float
    man_accessories: float
    optional_accessories : float
    booking: float
    total_price : float
    finance_amount: Optional[float] = None
    finance_id: Optional[int] = None
    
class CustomerForm(BaseModel):
    photo_adhaar_front: Optional[str] = None  # URL or S3 key for the Aadhaar front photo
    photo_adhaar_back: Optional[str] = None  # URL or S3 key for the Aadhaar back photo
    photo_passport: Optional[str] = None  # URL or S3 key for the passport photo
    vehicle_name: str
    vehicle_variant: str
    vehicle_color: Optional[str] = None
    ex_showroom_price: float
    tax: float
    onroad_price: float
    link_token: str  # Token from the generated link to identify the customer record

class CustomerOut(BaseModel):
    customer_id: int
    name: str
    first_name : Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    pin_code: Optional[str] = None
    phone_number: str
    alternate_phone_number: Optional[str] = None
    dob: Optional[date] = None
    nominee: Optional[str] = None
    relation: Optional[str] = None
    status: str
    branch_id: int
    photo_adhaar_front: Optional[str] = None  # URL or S3 key for the Aadhaar front photo
    photo_adhaar_back: Optional[str] = None  # URL or S3 key for the Aadhaar back photo
    photo_passport: Optional[str] = None
    customer_sign: Optional[str] = None  # URL or S3 key for the passport photo
    vehicle_name: Optional[str] = None  # Marked as optional
    vehicle_variant: Optional[str] = None  # Marked as optional
    vehicle_color: Optional[str] = None
    ex_showroom_price: Optional[float] = None  # Marked as optional
    tax: Optional[float] = None  # Marked as optional
    sales_verified: bool
    accounts_verified: bool
    rto_verified: Optional[bool] = None

    class Config:
        orm_mode = True
        from_attributes = True

class CustomerListResponse(BaseModel):
    customers: List[CustomerOut]

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
    


class TokenData(BaseModel):
    id: int

class FinanceCreate(BaseModel):
    company_name:str
    details: Optional[str]





class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    phone_number: str
    address: Optional[str] = None
    email: Optional[str]
    vehicle_name: str
    vehicle_variant: str
    vehicle_color: Optional[str] = None
    sales_verified: bool
    accounts_verified: bool
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class CustomerUpdatesales(BaseModel):
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: str
    status: Optional[str]
    vehicle_name: Optional[str] = None  
    vehicle_variant: Optional[str] = None  
    vehicle_color: Optional[str] = None
    ex_showroom_price: Optional[float] = None  
    tax: Optional[float] = None  
    onroad_price: Optional[float] = None  
    sales_verified: Optional[bool] = None

    class Config:
        orm_mode = True

class CustomerUpdate(BaseModel):
    name: str
    first_name : Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: str
    status: str
    photo_adhaar_front: Optional[str] = None  # URL or S3 key for the Aadhaar front photo
    photo_adhaar_back: Optional[str] = None  # URL or S3 key for the Aadhaar back photo
    photo_passport: Optional[str] = None  # URL or S3 key for the passport photo
    vehicle_name: Optional[str] = None  # Marked as optional
    vehicle_variant: Optional[str] = None  # Marked as optional
    vehicle_color: Optional[str] = None
    ex_showroom_price: Optional[float] = None  # Marked as optional
    tax: Optional[float] = None  # Marked as optional
    onroad_price: Optional[float] = None  # Marked as optional
    accounts_verified: Optional[bool]
    status: Optional[str]


class BranchCreate(BaseModel):
    name: str
    address: str
    phone_number: str
    branch_manager: str

class BranchUpdate(BaseModel):
    name: str
    address: str
    phone_number: str
    branch_manager: str

# Schema for returning branch information
class Branch(BaseModel):
    branch_id: int
    name: str
    address: Optional[str]
    branch_manager: Optional[str]
    phone_number: Optional[str]

    class Config:
        orm_mode = True

class BranchResponse(BaseModel):
    branch_id: int
    name: str
    address: str
    phone_number: str
    branch_manager: str

    class Config:
        orm_mode = True

class ChassisResponse(BaseModel):
    chassis_number: str
    chassis_photo_url: str
    class Config:
        orm_mode = True
