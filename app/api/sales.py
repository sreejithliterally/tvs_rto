from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
from schemas import CustomerResponse , CustomerUpdate

router = APIRouter()

@router.post("/sales/create-customer")
def create_customer(customer: schemas.CustomerBase, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customer_token = str(uuid4())
    print(customer_token)
    new_customer = models.Customer(
        name=customer.name,
        phone_number=customer.phone_number,
        link_token=customer_token,
        branch_id=current_user.branch_id,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        vehicle_color=customer.vehicle_color,
        ex_showroom_price= customer.ex_showroom_price,
        tax= customer.tax,
        onroad_price= customer.onroad_price
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    customer_link = f"http://localhost:3000/customer-form/{customer_token}"
    return {"customer_link": customer_link}

@router.post("/verify/sales/{customer_id}")
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


@router.get("/sales/customers", response_model=List[schemas.CustomerOut])
def get_customers_for_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id).all()

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
            "sales_verified": customer.sales_verified,
            "accounts_verified": customer.accounts_verified,
            "vehicle_name": customer.vehicle_name,
            "vehicle_variant": customer.vehicle_variant,
            "ex_showroom_price": customer.ex_showroom_price,
            "tax": customer.tax,
            "onroad_price": customer.onroad_price,
        }
        for customer in customers
    ]
    return customer_data


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, update_data: CustomerUpdate, db: Session = Depends(database.get_db)):
    # Fetch the customer from the database
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Update the customer fields with the provided data
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)

    return customer
