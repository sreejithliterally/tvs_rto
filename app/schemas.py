from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    branch_id: Optional[int] = None

class UserOut(BaseModel):
    username: str
    role:str
    branch_id: Optional[int] = None
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


class TokenData(BaseModel):
    id: int