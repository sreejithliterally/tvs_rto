from fastapi import APIRouter, Depends, HTTPException,UploadFile,File, Form
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
import utils

router = APIRouter()

@router.get("/customer/{token}")  # Provide the path in the decorator
def get_customer_by_token(token: str, db: Session = Depends(database.get_db)):
    customer = db.query(models.Customer).filter(models.Customer.token == token).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.post("/customer/{token}")
def submit_customer_form(
    token: str, 
    email: str = Form(...), 
    address: str = Form(...), 
    aadhaar_photo: UploadFile = File(...), 
    passport_photo: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    customer = db.query(models.Customer).filter(models.Customer.token == token).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    # Upload files to S3
    aadhaar_url = utils.upload_image_to_s3(aadhaar_photo, "hogspot")
    passport_url = utils.upload_image_to_s3(passport_photo, "hogspot")
    
    # Update customer info
    customer.email = email
    customer.address = address
    customer.photo_adhaar = aadhaar_url
    customer.photo_passport = passport_url
    customer.status = "submitted"

    db.commit()
    db.refresh(customer)
    
    return customer