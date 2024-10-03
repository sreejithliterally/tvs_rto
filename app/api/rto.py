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
    if user.role_id != 4:  # Assuming role_id 3 is for accounts role
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


@router.post("/verify/{customer_id}")
def verify_customer_rto(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # Ensure the user is a sales executive (role_id == 2 for sales executive)
    if current_user.role_id != 4:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Retrieve the customer by ID
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Update the customer verification status for sales
    customer.rto_verified = True
    
    # Log the verification action in the VerificationLog table
    verification_log = models.VerificationLog(
        user_id=current_user.user_id,
        customer_id=customer.customer_id,
        action="rto_verified"
    )
    
    db.add(verification_log)
    db.commit()

    return {"message": "Customer rto registration successful"}

