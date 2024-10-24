from io import BytesIO
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from typing import List, Optional
from sqlalchemy.orm import Session
import models, schemas, database, oauth2
from datetime import datetime
import utils
from .customer import compress_image
from .sales import generate_unique_filename

router = APIRouter(
    prefix="/rto",
    tags=["RTO"]
)


def is_user_in_rto_role(user: models.User):
    if user.role_id != 4:  # Assuming role_id 4 is for RTO role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )


@router.get("/verified-customers", response_model=List[schemas.CustomerOut])
def get_verified_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)

   
    customers = db.query(models.Customer).filter(models.Customer.rto_verified == True).all()

    return customers


@router.post("/verify/{customer_id}")
def verify_customer_rto(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)

    # Retrieve the customer by ID
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Check if the customer is eligible for RTO verification
    if not (customer.sales_verified and customer.accounts_verified):
        raise HTTPException(status_code=400, detail="Customer must be sales and accounts verified before RTO verification.")

    # Update the customer's RTO verification status
    customer.rto_verified = True

    # Log the verification action in the VerificationLog table
    verification_log = models.VerificationLog(
        user_id=current_user.user_id,
        customer_id=customer.customer_id,
        action="rto_verified",
        timestamp=datetime.utcnow()
    )

    db.add(verification_log)
    db.commit()

    return {"message": "Customer RTO registration successful"}


@router.put("/customers/{customer_id}", response_model=schemas.CustomerEditedResponse)
def update_customer(
    customer_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    vehicle_number: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_rto_role(current_user)
    
    # Retrieve the customer by ID
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

    if vehicle_number is not None:
        customer.vehicle_number = vehicle_number
        customer.registered = True

    db.commit()
    db.refresh(customer)

    return customer



@router.get("/pending-customers", response_model=List[schemas.CustomerOut])
def get_pending_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)

    # Fetch customers who are eligible for RTO verification
    customers = db.query(models.Customer).filter(
        models.Customer.sales_verified == True,
        models.Customer.accounts_verified == True,
        models.Customer.rto_verified == False
    ).all()

    if not customers:
        logging.info("No customers found matching the RTO criteria.")
    else:
        logging.info(f"Found {len(customers)} customers matching RTO criteria.")

    return customers


# Endpoint to get all customers eligible for RTO verification
@router.get("/customer-list", response_model=List[schemas.CustomerOut])
def get_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)
    
    # Fetch customers who are sales and accounts verified but not yet RTO verified
    customers = db.query(models.Customer).filter(
        models.Customer.sales_verified == True,
        models.Customer.accounts_verified == True,
        models.Customer.rto_verified == False
    ).all()
    
    return customers





@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer_by_id(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)

    
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found or you are not authorized to view this customer.")

    return customer








