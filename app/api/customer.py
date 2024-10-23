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


def compress_image(file: BytesIO, quality=85) -> BytesIO:
    image = Image.open(file)  # Now works with BytesIO directly
    
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
    
    # Remove white background from signature
    transparent_signature = remove_background(customer_sign)

    # Combine Aadhaar front and back photos vertically
    combined_aadhaar_image = combine_images_vertically(aadhaar_front_photo, aadhaar_back_photo)

    # Convert to BytesIO for compression
    aadhaar_combined_io = BytesIO(combined_aadhaar_image.read())
    passport_io = BytesIO(passport_photo.file.read())

    # Compress the images
    compressed_combined_aadhaar = compress_image(aadhaar_combined_io)
    compressed_passport = compress_image(passport_io)
    compressed_signature = compress_image(transparent_signature)
    customer_sign.file.seek(0)
    customer_sign_with_bg = BytesIO(customer_sign.file.read())
    compressed_signature_with_bg = compress_image(customer_sign_with_bg)

    # compressed_signature_copy = customer_sign

    # Generate unique filenames for each image
    aadhaar_combined_filename = generate_unique_filename("aadhaar_combined.jpg")
    passport_filename = generate_unique_filename(passport_photo.filename)
    signature_filename = generate_unique_filename("sign.png")
    signature_copy_filename = generate_unique_filename("signcopy.png")

    # Upload compressed images to S3 with unique filenames
    aadhaar_combined_url = await utils.upload_image_to_s3(compressed_combined_aadhaar, "hogspot", aadhaar_combined_filename)
    passport_url = await utils.upload_image_to_s3(compressed_passport, "hogspot", passport_filename)
    signature_url = await utils.upload_image_to_s3(compressed_signature, "hogspot", signature_filename)
    signature_copy_url = await utils.upload_image_to_s3(compressed_signature_with_bg, "hogspot", signature_copy_filename)

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
    customer.customer_sign_copy = signature_copy_url

    # Calculate balance_amount considering finance_amount if available
       # If finance details are not yet added, assume finance_amount is 0
    finance_amount = customer.finance_amount if customer.finance_amount is not None else Decimal("0.0")
    amount_paid = customer.amount_paid or Decimal("0.0")
    
    # Calculate the balance amount
    customer.balance_amount = customer.total_price - finance_amount - amount_paid

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
