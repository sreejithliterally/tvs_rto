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
from datetime import datetime

router = APIRouter(
    prefix="/customer",
    tags=["Customer"]
)
def combine_images_vertically(image1: UploadFile, image2: UploadFile) -> BytesIO:
    # Open both images
    image1 = Image.open(io.BytesIO(image1.file.read()))
    image2 = Image.open(io.BytesIO(image2.file.read()))
    
    # Get the width and height of both images
    width1, height1 = image1.size
    width2, height2 = image2.size

    # Create a new image with the width of the wider image and the combined height
    total_height = height1 + height2
    max_width = max(width1, width2)
    
    # Create a blank image for the combined result
    combined_image = Image.new("RGB", (max_width, total_height))
    
    # Paste the first image at the top and the second image below it
    combined_image.paste(image1, (0, 0))
    combined_image.paste(image2, (0, height1))
    
    # Save combined image to BytesIO
    combined_image_bytes = BytesIO()
    combined_image.save(combined_image_bytes, format='JPEG')
    combined_image_bytes.seek(0)
    
    return combined_image_bytes


def compress_image(uploaded_file: UploadFile, quality=85) -> BytesIO:
    image = Image.open(uploaded_file.file)
    
    # Convert the image to RGB if it's not (to ensure compatibility with JPEG)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    # Save the image into a BytesIO object
    compressed_image = BytesIO()
    image.save(compressed_image, format='JPEG', quality=quality)
    compressed_image.seek(0)  # Reset the file pointer to the beginning
    
    return compressed_image

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
def submit_customer_form(
    link_token: str,
    first_name: str = Form(...),
    last_name: str = Form(...), 
    dob: str = Form(...),
    email: str = Form(...), 
    address: str = Form(...), 
    pin_code: str = Form(...),
    nominee: str = Form(...),
    relation: str = Form(...),
    aadhaar_front_photo: UploadFile = File(...),
    aadhaar_back_photo: UploadFile = File(...),
    passport_photo: UploadFile = File(...),
    customer_sign: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # Fetch the customer based on the link token
    customer = db.query(models.Customer).filter(models.Customer.link_token == link_token).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    try:
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    

    combined_aadhaar_image = combine_images_vertically(aadhaar_front_photo, aadhaar_back_photo)
    compressed_combined_aadhaar = compress_image(UploadFile(file=combined_aadhaar_image))
    compressed_passport = compress_image(passport_photo)
    compressed_signature = compress_image(customer_sign)

    # Generate unique filenames for each image
    aadhaar_combined_filename = generate_unique_filename("aadhaar_combined.jpg")

    passport_filename = generate_unique_filename(passport_photo.filename)
    signature_filename = generate_unique_filename(customer_sign.filename)

    # Upload compressed images to S3 with unique filenames
    aadhaar_combined_url = utils.upload_image_to_s3(compressed_combined_aadhaar, "hogspot", aadhaar_combined_filename)
    passport_url = utils.upload_image_to_s3(compressed_passport, "hogspot", passport_filename)
    signature_url = utils.upload_image_to_s3(compressed_signature, "hogspot", signature_filename)

    # Update customer details
    customer.first_name = first_name
    customer.last_name = last_name
    customer.dob = dob
    customer.nominee = nominee
    customer.relation = relation
    customer.email = email
    customer.address = address
    customer.pin_code = pin_code
    customer.photo_adhaar_combined = aadhaar_combined_url
    customer.photo_passport = passport_url
    customer.customer_sign = signature_url

    # Calculate balance_amount considering finance_amount if available
    finance_amount = customer.finance_amount or Decimal("0.0")

    customer.status = "submitted"

    db.commit()
    db.refresh(customer)

    # Prepare full name for response
    full_name = f"{first_name} {last_name}"

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
