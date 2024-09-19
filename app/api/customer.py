from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException,UploadFile,File, Form
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
import utils
from PIL import Image

router = APIRouter(
    prefix="/customer",
    tags=["Customer"],
    dependencies=[Depends(oauth2.get_current_user)]
)


def compress_image(image_file: UploadFile, max_size_kb: int = 400) -> BytesIO:
    # Open the image file
    image = Image.open(image_file.file)

    # Compress image by adjusting quality and format
    buffer = BytesIO()
    quality = 85  # Start with quality of 85

    # Save the image to the buffer in JPEG format
    image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    # Reduce quality if the image size exceeds max_size_kb
    while buffer.tell() > max_size_kb * 1024:
        quality -= 5
        buffer = BytesIO()  # Clear the buffer
        image.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

    return buffer


@router.get("/customer-form/{link_token}")
def get_customer_data(link_token: str, db: Session = Depends(database.get_db)):
    # Query the customer by link_token
    customer = db.query(models.Customer).filter(models.Customer.link_token == link_token).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Return necessary customer details
    customer_data = {
        "name": customer.name,
        "phone_number": customer.phone_number,
        "vehicle_name": customer.vehicle_name,
        "vehicle_variant": customer.vehicle_variant,
        "vehicle_color": customer.vehicle_color,
        "ex_showroom_price": customer.ex_showroom_price,
        "tax": customer.tax,
        "onroad_price": customer.onroad_price
    }

    return customer_data


@router.post("/customer/{link_token}", response_model=schemas.CustomerResponse)
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
    
    # Compress images before uploading
    compressed_aadhaar_front = utils.compress_image(aadhaar_front_photo.file)
    compressed_aadhaar_back = utils.compress_image(aadhaar_back_photo.file)
    compressed_passport = utils.compress_image(passport_photo.file)

    # Upload compressed images to S3
    aadhaar_front_url = utils.upload_image_to_s3(compressed_aadhaar_front, "hogspot", "aadhaar_front.jpg")
    aadhaar_back_url = utils.upload_image_to_s3(compressed_aadhaar_back, "hogspot", "aadhaar_back.jpg")
    passport_url = utils.upload_image_to_s3(compressed_passport, "hogspot", "passport.jpg")

    # Update customer details
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
    
    # Prepare full name for response
    full_name = f"{first_name} {last_name}"
    
    return schemas.CustomerResponse(
        customer_id=customer.id,
        name=full_name,
        phone_number=customer.phone_number,
        email=customer.email,
        vehicle_name=customer.vehicle_name,
        sales_verified=customer.sales_verified,
        accounts_verified=customer.accounts_verified,
        status=customer.status,
        created_at=customer.created_at
    )
