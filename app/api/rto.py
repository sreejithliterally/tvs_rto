from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException,UploadFile,File, Form, status
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
import utils
from PIL import Image

router = APIRouter(
    prefix="/rto",
    tags=["Rto"]
    
)

def is_user_in_rto_role(user: models.User):
    if user.role_id != 3:  # Assuming role_id 3 is for accounts role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )


@router.get("/customer-list", response_model=List[schemas.CustomerOut])
def get_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)
    
    # Fetch customers only from the user's branch where sales are verified
    customers = db.query(models.Customer).filter(
        models.Customer.sales_verified == True,
        models.Customer.accounts_verified== True
    ).all()
    
    return customers