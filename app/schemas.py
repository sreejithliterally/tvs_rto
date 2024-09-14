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
    is_active: bool
    role_name: str

class CustomerBase(BaseModel):
    name: str
    phone_number: str

class CustomerForm(BaseModel):
    email: Optional[str]
    address: Optional[str]
    photo_adhaar: Optional[str]
    photo_passport: Optional[str]

class CustomerOut(BaseModel):
    cuurl: int
    name: str
    phone_number: str
    email: Optional[str]
    status: str
    branch_id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
    


class TokenData(BaseModel):
    id: int