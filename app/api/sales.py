from io import BytesIO
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form, status
from typing import List, Optional

from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2, utils
from schemas import CustomerResponse , CustomerUpdate, CustomerUpdatesales
from sqlalchemy import func
from datetime import datetime
from PIL import Image
from decimal import Decimal

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
    dependencies=[Depends(oauth2.get_current_user)]
)


def is_user_in_accounts_role(user: models.User):
    if user.role_id != 2:  
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )

@router.get("/balances", response_model=List[schemas.CustomerBalanceOut])
def get_pending_balances(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # Ensure the user is a sales executive
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Query customers with pending balances
    customers_with_pending_balances = db.query(models.Customer).filter(
        models.Customer.balance_amount > 0,
        models.Customer.branch_id == current_user.branch_id
    ).all()

    if not customers_with_pending_balances:
        raise HTTPException(status_code=404, detail="No customers with pending balances found.")

    return customers_with_pending_balances

def compress_image(uploaded_file: UploadFile, quality=85) -> BytesIO:
    image = Image.open(uploaded_file.file)
    
    
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


@router.put("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    sales_verified: Optional[bool] = Form(None),
    amount_paid: Optional[float] = Form(None),  # New field for updating amount_paid
    photo_adhaar_front: Optional[UploadFile] = File(None),
    photo_adhaar_back: Optional[UploadFile] = File(None),
    photo_passport: Optional[UploadFile] = File(None),
    customer_sign: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db)
):
    # Fetch the customer from the database
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
    if address is not None:
        customer.address = address
    if status is not None:
        customer.status = status
    if sales_verified is not None:
        customer.sales_verified = sales_verified
    if amount_paid is not None:
        # Convert amount_paid to Decimal for compatibility
        amount_paid_decimal = Decimal(str(amount_paid))
        customer.amount_paid = amount_paid_decimal

        # Calculate the balance considering the finance amount if applicable
        finance_amount = customer.finance_amount if customer.finance_amount else Decimal("0.0")
        customer.balance_amount = customer.total_price - finance_amount - amount_paid_decimal

    # Handle file uploads if they are provided
    if photo_adhaar_front is not None:
        compressed_aadhaar_front = compress_image(photo_adhaar_front)
        aadhaar_front_filename = generate_unique_filename(photo_adhaar_front.filename)
        customer.photo_adhaar_front = utils.upload_image_to_s3(compressed_aadhaar_front, "hogspot", aadhaar_front_filename)

    if photo_adhaar_back is not None:
        compressed_aadhaar_back = compress_image(photo_adhaar_back)
        aadhaar_back_filename = generate_unique_filename(photo_adhaar_back.filename)
        customer.photo_adhaar_back = utils.upload_image_to_s3(compressed_aadhaar_back, "hogspot", aadhaar_back_filename)

    if photo_passport is not None:
        compressed_passport = compress_image(photo_passport)
        passport_filename = generate_unique_filename(photo_passport.filename)
        customer.photo_passport = utils.upload_image_to_s3(compressed_passport, "hogspot", passport_filename)

    if customer_sign is not None:
        compressed_sign = compress_image(customer_sign)
        sign_filename = generate_unique_filename(customer_sign.filename)
        customer.customer_sign = utils.upload_image_to_s3(compressed_sign, "hogspot", sign_filename)

    db.commit()
    db.refresh(customer)

    # Prepare the response in the expected format
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
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customer_token = str(uuid4())
    print(customer_token)

    # Convert inputs to Decimal for accurate calculations
    total_price = Decimal(customer.total_price)
    amount_paid = Decimal("0.0")  # Initialize amount_paid to 0
    finance_amount = Decimal(customer.finance_amount) if customer.finance_amount else Decimal("0.0")

    # Calculate the balance amount considering the finance amount
    balance_amount = total_price - finance_amount - amount_paid

    new_customer = models.Customer(
        name=customer.name,
        phone_number=customer.phone_number,
        alternate_phone_number=customer.alternate_phone_number,
        link_token=customer_token,
        branch_id=current_user.branch_id,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        vehicle_color=customer.vehicle_color,
        ex_showroom_price=Decimal(customer.ex_showroom_price),
        tax=Decimal(customer.tax),
        insurance=Decimal(customer.insurance),
        tp_registration=Decimal(customer.tp_registration),
        man_accessories=Decimal(customer.man_accessories),
        optional_accessories=Decimal(customer.optional_accessories),
        total_price=total_price,
        booking=Decimal(customer.booking),
        finance_amount=finance_amount,
        sales_executive_id=current_user.user_id,
        finance_id=customer.finance_id if customer.finance_id else None,
        amount_paid=amount_paid,
        balance_amount=balance_amount,
        status="pending"
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    customer_link = f"http://192.168.29.198:3000/customer-form/{customer_token}"
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


@router.get("/customers", response_model=List[schemas.CustomerOut])
def get_customers_for_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id).all()

    #will return the customers' data relevant to the sales executive
    customer_data = [
        {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "address": customer.address,
            "phone_number": customer.phone_number,
            "status": customer.status,
            "branch_id": customer.branch_id,
            "photo_adhaar_front":customer.photo_adhaar_front,
            "photo_adhaar_back":customer.photo_adhaar_back,
            "photo_passport":customer.photo_passport,
            "customer_sign":customer.customer_sign,
            "sales_verified": customer.sales_verified,
            "accounts_verified": customer.accounts_verified,
            "vehicle_name": customer.vehicle_name,
            "vehicle_variant": customer.vehicle_variant,
            "ex_showroom_price": customer.ex_showroom_price,
            "tax": customer.tax
        }
        for customer in customers
    ]
    return customer_data


@router.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
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


    customer_data = {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "address": customer.address,
        "phone_number": customer.phone_number,
        "status": customer.status,
        "branch_id": customer.branch_id,
        "photo_adhaar_front": customer.photo_adhaar_front,
        "photo_adhaar_back": customer.photo_adhaar_back,
        "photo_passport": customer.photo_passport,
        "customer_sign": customer.customer_sign,
        "sales_verified": customer.sales_verified,
        "accounts_verified": customer.accounts_verified,
        "vehicle_name": customer.vehicle_name,
        "vehicle_variant": customer.vehicle_variant,
        "ex_showroom_price": customer.ex_showroom_price,
        "tax": customer.tax
    }

    return customer_data

