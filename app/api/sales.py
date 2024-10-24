from io import BytesIO
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form, status
from typing import List, Optional
import utils
import io
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2, utils
from schemas import CustomerResponse , CustomerUpdate, CustomerUpdatesales
from sqlalchemy import func
from datetime import datetime
from PIL import Image
from decimal import Decimal
import cv2
import numpy as np


router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
    dependencies=[Depends(oauth2.get_current_user)]
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


def is_user_in_sales_role(user: models.User):
    if user.role_id != 2:  # Ensure the user is a sales executive
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )
def generate_unique_filename(original_filename: str) -> str:
    ext = original_filename.split('.')[-1]  # Get the file extension
    unique_name = f"{uuid.uuid4()}.{ext}"  # Create a unique filename with the same extension
    return unique_name

@router.get("/balances", response_model=List[schemas.CustomerBalanceOut])
def get_pending_balances(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_sales_role(current_user)
    
    customers_with_pending_balances = db.query(models.Customer).filter(
        models.Customer.balance_amount > 0,
        models.Customer.branch_id == current_user.branch_id
    ).all()

    if not customers_with_pending_balances:
        raise HTTPException(status_code=404, detail="No customers with pending balances found.")

    return customers_with_pending_balances


async def compress_image(uploaded_file: UploadFile, quality=85) -> BytesIO:
    # Read the file contents of the UploadFile object
    file_bytes = await uploaded_file.read()  # Ensure we read the content as bytes
    
    # Convert it into a BytesIO stream
    file_stream = BytesIO(file_bytes)
    
    # Open the image using PIL
    image = Image.open(file_stream)

    # Convert to RGB if the image is not in that format
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
        
    # Compress the image into another BytesIO stream
    compressed_image = BytesIO()
    image.save(compressed_image, format='JPEG', quality=quality)
    compressed_image.seek(0)  # Reset the file pointer to the beginning

    return compressed_image



def generate_unique_filename(original_filename: str) -> str:
    ext = original_filename.split('.')[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    return unique_name


@router.post("/customers/delivery-update/{customer_id}", response_model=schemas.CustomerResponse)
async def update_customer(
    customer_id: int,
    number_plate_front: UploadFile = File(...),
    number_plate_back: UploadFile = File(...),
    delivery_photo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_sales_role(current_user)

    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    number_plate_front_filename = generate_unique_filename(number_plate_front.filename)
    number_plate_back_filename = generate_unique_filename(number_plate_back.filename)
    delivery_photo_filename = generate_unique_filename(delivery_photo.filename)

    # Read the contents of UploadFile and wrap it in BytesIO
    number_plate_front_bytes = BytesIO(await number_plate_front.read())
    number_plate_back_bytes = BytesIO(await number_plate_back.read())
    delivery_photo_bytes = BytesIO(await delivery_photo.read())

    # Call your upload function with the BytesIO objects
    number_plate_front_url = await utils.upload_image_to_s3(number_plate_front_bytes, "hogspot", number_plate_front_filename)
    number_plate_back_url = await utils.upload_image_to_s3(number_plate_back_bytes, "hogspot", number_plate_back_filename)
    delivery_photo_url = await utils.upload_image_to_s3(delivery_photo_bytes, "hogspot", delivery_photo_filename)

    customer.number_plate_front = number_plate_front_url
    customer.number_plate_back = number_plate_back_url
    customer.delivery_photo = delivery_photo_url

    db.commit()
    db.refresh(customer)
    return customer





@router.put("/customers/update-adhaar/{customer_id}", response_model=schemas.CustomerResponse)
async def update_customer(
    customer_id: int,
    aadhaar_front_photo: UploadFile = File(...),
    aadhaar_back_photo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_sales_role(current_user)
    
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    combined_aadhaar_image = combine_images_vertically(aadhaar_front_photo, aadhaar_back_photo)
    aadhaar_combined_io = BytesIO(combined_aadhaar_image.read())
    compressed_combined_aadhaar = compress_image(aadhaar_combined_io)
    aadhaar_combined_filename = generate_unique_filename("aadhaar_combined.jpg")
    aadhaar_combined_url = await utils.upload_image_to_s3(compressed_combined_aadhaar, "hogspot", aadhaar_combined_filename)
    customer.photo_adhaar_combined = aadhaar_combined_url
    db.commit()
    db.refresh(customer)
    return customer

@router.put("/customers/update-passport-photo/{customer_id}", response_model=schemas.CustomerResponse)
async def update_customer(
    customer_id: int,
    passport_photo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_sales_role(current_user)
    
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    passport_io = BytesIO(passport_photo.file.read())
    compressed_passport = compress_image(passport_io)
    passport_compressed_filename = generate_unique_filename("passport.jpg")
    passport_url =await utils.upload_image_to_s3(compressed_passport, "hogspot", passport_compressed_filename)
    customer.photo_passport = passport_url
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/customers/update-customersign/{customer_id}", response_model=schemas.CustomerResponse)
async def update_customer_sign(
    customer_id: int,
    customer_sign: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_sales_role(current_user)
    
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Compress the signature image
    compressed_sign = await compress_image(customer_sign)

    # Generate unique filename and upload compressed image to S3
    sign_compressed_filename = generate_unique_filename("sign.png")
    sign_url = await utils.upload_image_to_s3(compressed_sign, "hogspot", sign_compressed_filename)

    # Update customer with the new signature URL
    customer.customer_sign = sign_url

    db.commit()
    db.refresh(customer)

    return customer



@router.put("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    alternate_phone_number: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),  # Assuming this is in string format (YYYY-MM-DD)
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    pin_code: Optional[str] = Form(None),
    nominee: Optional[str] = Form(None),
    relation: Optional[str] = Form(None),
    vehicle_name: Optional[str] = Form(None),
    vehicle_variant: Optional[str] = Form(None),
    vehicle_color: Optional[str] = Form(None),
    ex_showroom_price: Optional[float] = Form(None),
    tax: Optional[float] = Form(None),
    insurance: Optional[float] = Form(None),
    tp_registration: Optional[float] = Form(None),
    man_accessories: Optional[float] = Form(None),
    optional_accessories: Optional[float] = Form(None),
    amount_paid: Optional[float] = Form(None),
    vehicle_number: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Check user role
    is_user_in_sales_role(current_user)
    
    # Fetch customer record
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Update fields if values are provided
    if first_name is not None:
        customer.first_name = first_name
    if last_name is not None:
        customer.last_name = last_name
    if phone_number is not None:
        customer.phone_number = phone_number
    if alternate_phone_number is not None:
        customer.alternate_phone_number = alternate_phone_number
    if dob is not None:
        try:
            customer.dob = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    if email is not None:
        customer.email = email
    if address is not None:
        customer.address = address
    if pin_code is not None:
        customer.pin_code = pin_code
    if nominee is not None:
        customer.nominee = nominee
    if relation is not None:
        customer.relation = relation
    if vehicle_name is not None:
        customer.vehicle_name = vehicle_name
    if vehicle_variant is not None:
        customer.vehicle_variant = vehicle_variant
    if vehicle_color is not None:
        customer.vehicle_color = vehicle_color

    # Update price-related fields and total price
    if ex_showroom_price is not None:
        customer.ex_showroom_price = Decimal(str(ex_showroom_price))
    if tax is not None:
        customer.tax = Decimal(str(tax))
    if insurance is not None:
        customer.insurance = Decimal(str(insurance))
    if tp_registration is not None:
        customer.tp_registration = Decimal(str(tp_registration))
    if man_accessories is not None:
        customer.man_accessories = Decimal(str(man_accessories))
    if optional_accessories is not None:
        customer.optional_accessories = Decimal(str(optional_accessories))

    # Recalculate total price only if relevant fields are updated
    if (
        ex_showroom_price is not None or tax is not None or insurance is not None or
        tp_registration is not None or man_accessories is not None or optional_accessories is not None
    ):
        customer.total_price = (
            customer.ex_showroom_price +
            customer.tax +
            customer.insurance +
            customer.tp_registration +
            customer.man_accessories +
            customer.optional_accessories
        )

    # Handle amount_paid and balance_amount
    if amount_paid is not None:
        amount_paid_decimal = Decimal(str(amount_paid))
        customer.amount_paid = amount_paid_decimal
        customer.balance_amount = customer.total_price - amount_paid_decimal
    else:
        # Recalculate balance if only total_price was updated
        customer.balance_amount = customer.total_price - customer.amount_paid

    # Update vehicle number
    if vehicle_number is not None:
        customer.vehicle_number = vehicle_number

    # Commit changes to the database
    db.commit()
    db.refresh(customer)

    # Prepare response
    full_name = f"{customer.first_name} {customer.last_name}"
    return schemas.CustomerResponse(
        customer_id=customer.customer_id,
        name=full_name,
        phone_number=customer.phone_number,
        address=customer.address,
        email=customer.email,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        vehicle_color=customer.vehicle_color,
        sales_verified=customer.sales_verified,
        accounts_verified=customer.accounts_verified,
        rto_verified=customer.rto_verified,
        registered=customer.registered,
        status=customer.status,
        created_at=customer.created_at,
        amount_paid=customer.amount_paid,
        balance_amount=customer.balance_amount
    )


@router.post("/create-customer")
def create_customer(
    customer: schemas.CustomerBase,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_sales_role(current_user)
    
    customer_token = str(uuid4())
    print(customer_token)

    # Convert inputs to Decimal for accurate calculations
    ex_showroom_price = Decimal(customer.ex_showroom_price)
    tax = Decimal(customer.tax)
    insurance = Decimal(customer.insurance)
    tp_registration = Decimal(customer.tp_registration)
    man_accessories = Decimal(customer.man_accessories)
    optional_accessories = Decimal(customer.optional_accessories)
    booking = Decimal(customer.booking)

    # Calculate the total price based on the input fields
    total_price = (
        ex_showroom_price +
        tax +
        insurance +
        tp_registration +
        man_accessories +
        optional_accessories
    )

    # Use the amount_paid provided by the sales executive
    amount_paid = Decimal(customer.amount_paid or "0.0")

    # Calculate the balance amount
    balance_amount = total_price - amount_paid

    customer_link = f"https://192.168.29.199:3000/customer-form/{customer_token}"

    new_customer = models.Customer(
        name=customer.name,
        phone_number=customer.phone_number,
        alternate_phone_number=customer.alternate_phone_number,
        link = customer_link,
        link_token=customer_token,
        branch_id=current_user.branch_id,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        vehicle_color=customer.vehicle_color,
        ex_showroom_price=ex_showroom_price,
        tax=tax,
        insurance=insurance,
        tp_registration=tp_registration,
        man_accessories=man_accessories,
        optional_accessories=optional_accessories,
        total_price=total_price,
        booking=booking,
        amount_paid=amount_paid,
        balance_amount=balance_amount,
        sales_executive_id=current_user.user_id,
        status="pending"
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    
    return {"customer_link": customer_link}



@router.get("/customer-verification/count")
def customer_review_count_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    review_pending = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.sales_verified==False,
                                                 models.Customer.status=='submitted').count()
    review_done = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.sales_verified==True).count()
    return {
        "reviews pending":review_pending,
        "reviews Done":review_done
    }


@router.get("/customers/count")
def get_customer_count_for_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    total_customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id).count()
    
    total_pending_customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.status=="pending").count()
    total_submitted_customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.status=="submitted").count()
    
    
    
    return {"total_count":total_customers,
            "total_pending": total_pending_customers,
            "total_submitted": total_submitted_customers
            }

@router.get("/customers/count_per_day")
def get_customer_count_per_day(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:  # Check if the user is a sales executive
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Query to get count of customers generated per day for the current sales executive
    customer_count_per_day = (
        db.query(func.date(models.Customer.created_at), func.count(models.Customer.customer_id))
        .filter(models.Customer.branch_id == current_user.branch_id,
                models.Customer.sales_executive_id == current_user.user_id)
        .group_by(func.date(models.Customer.created_at))  # Group by the date part of created_at
        .order_by(func.date(models.Customer.created_at))  # Sort by date
        .all()
    )

    # Structure the result as a list of dictionaries for easier consumption in the frontend
    result = [{"date": date.strftime('%Y-%m-%d'), "count": count} for date, count in customer_count_per_day]

    return {"data": result}


@router.post("/verify/{customer_id}")
def verify_customer_sales(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # Ensure the user is a sales executive (role_id == 2 for sales executive)
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Retrieve the customer by ID
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Update the customer verification status for sales
    customer.sales_verified = True
    
    # Log the verification action in the VerificationLog table
    verification_log = models.VerificationLog(
        user_id=current_user.user_id,
        customer_id=customer.customer_id,
        action="sales_verified"
    )
    
    db.add(verification_log)
    db.commit()

    return {"message": "Customer sales verification completed."}


@router.get("/customers", response_model=List[schemas.CustomerOutSales])
def get_customers_for_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id).all()

    #will return the customers' data relevant to the sales executive
    return customers


@router.get("/customers/{customer_id}", response_model=schemas.CustomerOutSales)
def get_customer_by_id(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:

        raise HTTPException(status_code=403, detail="Not authorized.")

    customer = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id,  
        models.Customer.branch_id == current_user.branch_id,  
        models.Customer.sales_executive_id == current_user.user_id  
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found or you are not authorized to view this customer.")


    return customer

