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

def combine_images_vertically(cropped_image1: BytesIO, cropped_image2: BytesIO) -> BytesIO:
    # Load the cropped images from BytesIO
    image1 = Image.open(cropped_image1)
    image2 = Image.open(cropped_image2)
    
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


async def compress_image(file, min_size_kb=300, max_size_kb=400) -> BytesIO:
    # Check if input is `UploadFile`; if so, read it into `bytes`
    if isinstance(file, UploadFile):
        file_bytes = await file.read()  # Use await if it's an UploadFile
        file_stream = BytesIO(file_bytes)
    elif isinstance(file, BytesIO):
        file_stream = file  # Already a BytesIO object
    else:
        raise TypeError("Unsupported file type. Must be UploadFile or BytesIO.")

    # Open the image using PIL
    image = Image.open(file_stream)

    # Convert to RGB if necessary
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    quality = 85
    compressed_image = BytesIO()

    while True:
        compressed_image.seek(0)
        compressed_image.truncate(0)
        
        image.save(compressed_image, format='JPEG', quality=quality)
        size_kb = compressed_image.tell() / 1024
        
        # Check size constraints
        if min_size_kb <= size_kb <= max_size_kb:
            break
        elif size_kb < min_size_kb:
            quality += 5
        else:
            quality -= 5

        if quality < 10 or quality > 95:
            break

    compressed_image.seek(0)
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
async def submit_customer_form(
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
    
    
    passport_io = BytesIO(passport_photo.file.read())
    aadhaar_front_io = BytesIO(aadhaar_front_photo.file.read())
    aadhaar_back_io = BytesIO(aadhaar_back_photo.file.read())
    # Combine the cropped Aadhaar front and back images

    # Convert combined Aadhaar to BytesIO for compression
    compressed_passport = await compress_image(passport_io)
    transparent_signature = remove_background(customer_sign)
    compressed_signature = await compress_image(transparent_signature)

    # Generate unique filenames
    aadhaar_front_filename = generate_unique_filename("aadhaarfront.jpg")
    aadhaar_back_filename = generate_unique_filename("aadhaarback.jpg")

    passport_filename = generate_unique_filename(passport_photo.filename)
    signature_filename = generate_unique_filename("sign.png")

    # Upload images to S3
    aadhaar_front_url = await utils.upload_image_to_s3(aadhaar_front_io, "hogspot", aadhaar_front_filename)
    aadhaar_back_url = await utils.upload_image_to_s3(aadhaar_back_io, "hogspot", aadhaar_back_filename)
    passport_url = await utils.upload_image_to_s3(compressed_passport, "hogspot", passport_filename)
    signature_url = await utils.upload_image_to_s3(compressed_signature, "hogspot", signature_filename)

    # Update customer details
    customer.first_name = first_name
    customer.last_name = last_name
    customer.dob = dob
    customer.nominee = nominee
    customer.relation = relation
    customer.email = email
    customer.address = address
    customer.pin_code = pin_code
    customer.adhaar_front = aadhaar_front_url
    customer.adhaar_back = aadhaar_back_url
    customer.photo_passport = passport_url
    customer.customer_sign = signature_url

    # Calculate balance amount
    finance_amount = customer.finance_amount or Decimal("0.0")
    amount_paid = customer.amount_paid or Decimal("0.0")
    customer.balance_amount = customer.total_price - finance_amount - amount_paid
    customer.status = "submitted"

    db.commit()
    db.refresh(customer)

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
