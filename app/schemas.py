from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

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
    vehicle_name: str
    vehicle_variant: str
    vehicle_color: Optional[str] = None
    ex_showroom_price: float
    tax: float
    onroad_price: float

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
    phone_number: str
    status: str
    branch_id: int
    sales_verified: bool
    accounts_verified: bool

    class Config:
        orm_mode = True
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
    


class TokenData(BaseModel):
    id: int




class CustomerUpdate(BaseModel):
    name: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    vehicle_name: Optional[str]
    sales_verified: Optional[bool]
    accounts_verified: Optional[bool]
    status: Optional[str]

class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    phone_number: str
    email: Optional[str]
    vehicle_name: str
    sales_verified: bool
    accounts_verified: bool
    status: str
    created_at: datetime

    class Config:
        orm_mode = True