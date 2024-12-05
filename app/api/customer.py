from io import BytesIO
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
import utils
import uuid
from PIL import Image
import cv2
import numpy as np
import logging

from datetime import datetime

router = APIRouter(
    prefix="/customer",
    tags=["Customer"]
)

def remove_background(image: UploadFile) -> BytesIO:
    # Read the uploaded image as a numpy array using OpenCV
    file_bytes = np.frombuffer(image.file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)

    # Define a threshold for the background
    thresh = 110
    
    # Threshold the image to create a binary image
    _, img_thresh = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY)

    # Convert the thresholded image back to PIL Image for further processing
    img_pil = Image.fromarray(img_thresh).convert("RGBA")
    
    # Load the pixel data from the image
    pixdata = img_pil.load()

    # Get the width and height of the image
    width, height = img_pil.size

    # Loop over the pixels and make the white pixels transparent
    for y in range(height):
        for x in range(width):
            if pixdata[x, y] == (255, 255, 255, 255):  # White pixel
                pixdata[x, y] = (255, 255, 255, 0)     # Make transparent

    # Save the modified image to a BytesIO object
    transparent_image_io = BytesIO()
    img_pil.save(transparent_image_io, format="PNG")
    transparent_image_io.seek(0)

    return transparent_image_io







# Function to generate a unique filename
def generate_unique_filename(original_filename: str) -> str:
    ext = original_filename.split('.')[-1]  # Get the file extension
    unique_name = f"{uuid.uuid4()}.{ext}"  # Create a unique filename with the same extension
    return unique_name


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
        "insurance": customer.insurance,
        "tp_registration": customer.tp_registration,
        "man_accessories": customer.man_accessories,
        "optional_accessories": customer.optional_accessories,
        "total_price": customer.total_price,
        "booking": customer.booking,
        "finance_amount": customer.finance_amount,
    }

    return customer_data


@router.post("/{link_token}", response_model=schemas.CustomerResponse)
async def submit_customer_form(
    link_token: str,
    first_name: str = Form(None),
    last_name: str = Form(None),
    dob: str = Form(None),
    email: str = Form(None),
    address: str = Form(None),
    pin_code: str = Form(None),
    nominee: str = Form(None),
    relation: str = Form(None),
    aadhaar_front_photo: UploadFile = File(None),
    aadhaar_back_photo: UploadFile = File(None),
    passport_photo: UploadFile = File(None),
    customer_sign: UploadFile = File(None),
    db: Session = Depends(database.get_db)
):
    # Fetch the customer based on the link token
    customer = db.query(models.Customer).filter(models.Customer.link_token == link_token).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Check for dob format if provided
    if dob:
        try:
            dob = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Process files only if they are provided
    if passport_photo:
        passport_io = BytesIO(passport_photo.file.read())
        compressed_passport = await utils.compress_image(passport_io)
        passport_filename = generate_unique_filename(passport_photo.filename)
        passport_url = await utils.upload_image_to_s3(compressed_passport, "tvstophaven", passport_filename)
        customer.photo_passport = passport_url

    if aadhaar_front_photo:
        aadhaar_front_io = BytesIO(aadhaar_front_photo.file.read())
        aadhaar_front_filename = generate_unique_filename("aadhaarfront.jpg")
        aadhaar_front_url = await utils.upload_image_to_s3(aadhaar_front_io, "tvstophaven", aadhaar_front_filename)
        customer.adhaar_front = aadhaar_front_url

    if aadhaar_back_photo:
        aadhaar_back_io = BytesIO(aadhaar_back_photo.file.read())
        aadhaar_back_filename = generate_unique_filename("aadhaarback.jpg")
        aadhaar_back_url = await utils.upload_image_to_s3(aadhaar_back_io, "tvstophaven", aadhaar_back_filename)
        customer.adhaar_back = aadhaar_back_url

    if customer_sign:
        transparent_signature = remove_background(customer_sign)
        compressed_signature = await utils.compress_image(transparent_signature)
        signature_filename = generate_unique_filename("sign.png")
        signature_url = await utils.upload_image_to_s3(compressed_signature, "tvstophaven", signature_filename)
        customer.customer_sign = signature_url

        # Optional copy of the signature
        customer_sign.file.seek(0)
        signature_copy = BytesIO(customer_sign.file.read())
        compressed_signature_copy = await utils.compress_image(signature_copy)
        signature_copy_filename = generate_unique_filename("copysign")
        signature_copy_url = await utils.upload_image_to_s3(compressed_signature_copy, "tvstophaven", signature_copy_filename)
        customer.customer_sign_copy = signature_copy_url

    # Update customer details only if provided
    customer.first_name = first_name if first_name else customer.first_name
    customer.last_name = last_name if last_name else customer.last_name
    customer.dob = dob if dob else customer.dob
    customer.nominee = nominee if nominee else customer.nominee
    customer.relation = relation if relation else customer.relation
    customer.email = email if email else customer.email
    customer.address = address if address else customer.address
    customer.pin_code = pin_code if pin_code else customer.pin_code

    # Calculate balance amount
    finance_amount = customer.finance_amount or Decimal("0.0")
    amount_paid = customer.amount_paid or Decimal("0.0")
    customer.balance_amount = customer.total_price - finance_amount - amount_paid
    customer.status = "submitted"

    db.commit()
    db.refresh(customer)

    full_name = f"{first_name} {last_name}" if first_name and last_name else customer.first_name or ""

    return schemas.CustomerResponse(
        customer_id=customer.customer_id,
        name=full_name,
        phone_number=customer.phone_number,
        address=customer.address,
        email=customer.email,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        sales_verified=customer.sales_verified,
        accounts_verified=customer.accounts_verified,
        status=customer.status,
        created_at=customer.created_at,
        balance_amount=customer.balance_amount
    )
