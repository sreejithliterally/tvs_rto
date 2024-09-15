from fastapi import APIRouter, Depends, HTTPException,UploadFile,File, Form
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
import utils

router = APIRouter()

@router.get("/customer-data/{link_token}")
def get_customer_data(link_token: str, db: Session = Depends(database.get_db)):
    # Find the customer by the link token
    customer = db.query(models.Customer).filter(models.Customer.link_token == link_token).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Return the basic customer info for greeting
    return {
        "name": f"{customer.first_name} {customer.last_name}",
        "vehicle_name": customer.vehicle_name,
        "vehicle_variant": customer.vehicle_variant
    }



@router.post("/customer/{token}")
def submit_customer_form(
    link_token: str,
    first_name: str = Form(...),
    last_name: str = Form(...), 
    email: str = Form(...), 
    address: str = Form(...), 
    aadhaar_front_photo: UploadFile = File(...),
    aadhaar_back_photo: UploadFile = File(...),
    passport_photo: UploadFile = File(...),

    db: Session = Depends(database.get_db)
):
    customer = db.query(models.Customer).filter(models.Customer.link_token == link_token).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    # Upload files to S3
    aadhaar_front_url = utils.upload_image_to_s3(aadhaar_front_photo, "hogspot")
    aadhaar_back_url = utils.upload_image_to_s3(aadhaar_back_photo, "hogspot")
    passport_url = utils.upload_image_to_s3(passport_photo, "hogspot")
    customer.first_name = first_name
    customer.last_name = last_name
    customer.email = email
    customer.address = address
    customer.photo_adhaar_front = aadhaar_front_url
    customer.photo_adhaar_back = aadhaar_back_url
    customer.photo_passport = passport_url

    customer.status = "submitted"

    db.commit()
    db.refresh(customer)
    
    return customer